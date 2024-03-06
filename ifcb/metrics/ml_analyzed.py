import os
import pandas as pd
import numpy as np

from ifcb.data.adc import SCHEMA_VERSION_1, SCHEMA_VERSION_2

FLOW_RATE = 0.25 # milliliters per minute for syringe pump

def compute_ml_analyzed_s1_adc(adc, min_proc_time=0.073):
    """compute ml_analyzed for an old instrument"""
    # first, make sure this isn't an empty bin
    if len(adc) == 0:
        return np.nan, np.nan, np.nan
    # we have targets, can proceed
    STEPS_PER_SEC = 40.
    ML_PER_STEP = 5./48000.
    FLOW_RATE = ML_PER_STEP * STEPS_PER_SEC # ml/s
    s = SCHEMA_VERSION_1
    adc = adc.drop_duplicates(subset=s.TRIGGER, keep='first')
    # handle case of bins that span midnight
    # these have negative frame grab and trigger open times
    # that need to have 24 hours added to them
    neg_adj = (adc[s.FRAME_GRAB_TIME] < 0) * 24*60*60.
    frame_grab_time = adc[s.FRAME_GRAB_TIME] + neg_adj
    neg_adj = (adc[s.TRIGGER_OPEN_TIME] < 0) * 24*60*60.
    trigger_open_time = adc[s.TRIGGER_OPEN_TIME] + neg_adj
    # done with that case
    # run time is assumed to be final frame grab time
    run_time = frame_grab_time.iloc[-1]
    # proc time is time between trigger open time and previous
    # frame grab time
    proc_time = np.array(trigger_open_time.iloc[1:]) - np.array(frame_grab_time[:-1])
    # set all proc times that are less than min to min
    proc_time[proc_time < min_proc_time] = min_proc_time
    # look time is run time - proc time
    # not sure why subtracting min_proc_time here is necessary
    # to match output from MATLAB code, that code may have a bug
    look_time = run_time - proc_time.sum() - min_proc_time
    # ml analyzed is look time times flow rate
    ml_analyzed = look_time * FLOW_RATE
    return ml_analyzed, look_time, run_time

def compute_ml_analyzed_s2_adc(adc):
    """
    This function returns the estimate of sample volume analyzed (in milliliters),
    assuming a standard IFCB configuration with the sample syringe operating at 0.25 mL per minute.
    It applies only to IFCB instruments after 007 and higher (except 008).
    """

    column_names = ['trigger', 'adc_time', 'pmt_a', 'pmt_b', 'pmt_c', 'pmt_d', 'peak_a', 'peak_b', 'peak_c', 'peak_d', 'time_of_flight', 'grabtime_start', 'grabtime_end', 'roi_x', 'roi_y', 'roi_width', 'roi_height', 'start_byte', 'comparator_out', 'start_point', 'signal_length', 'status', 'runtime', 'inhibit_time']
    adc.columns = column_names

    # if there are no records or the inhibit time is all 0, return NaN
    if adc.empty or adc['inhibit_time'].sum() == 0:
        return np.nan, np.nan, np.nan

    diffinh = np.diff(adc['inhibit_time'])

    # find indices of rows where inhibitime is not 0 and not less than the previous value (within 0.1 second)
    iii = np.where((adc['inhibit_time'][1:] > 0) & (diffinh > -0.1) & (diffinh < 5))[0] + 1
    iii = np.insert(iii, 0, 0)


    # calculate the mode differential inhibittime from the good records, round to nearest 4 digits before finding mode
    # this will be used as the "second best" estimate of the inhibittime for the whole file
    rounded_diffinh = round(pd.Series(np.diff(adc.loc[iii+1, 'inhibit_time'])), 4)
    modeinhibittime = rounded_diffinh.mode().values[0]
    
    runtime_offset = 0
    inhibittime_offset = 0

    if adc.shape[0] > 1: # if there is more than one row in the file
        # calculate the offset between runtime and adc_time for the first record
        runtime_offset_test = adc['runtime'].iloc[1] - adc['adc_time'].iloc[1]

        # if the offset is greater than 10 seconds, use it as the offset for the whole file
        if runtime_offset_test > 10:
            runtime_offset = runtime_offset_test
            # use the second row since the first one is bad occasionally, add two mode increments to account for that
            inhibittime_offset = adc['inhibit_time'].iloc[1] + modeinhibittime * 2

        if adc.shape[0] == len(iii): # if all records are good
            # inhibittime is the last record's inhibit_time minus the offset
            # this is the best value--if it's not bad
            inhibittime = adc['inhibit_time'].iloc[-1] - inhibittime_offset
        else:
            # second best estimate, last good row, plus mode as best guess for each bad row
            inhibittime = adc['inhibit_time'].iloc[iii[-1]] + (adc.shape[0] - len(iii)) * modeinhibittime - inhibittime_offset

        # runtime is the last record's runtime minus the offset
        runtime = adc['runtime'].iloc[-1] - runtime_offset

        n = min(adc.shape[0], 50) # use the first 50 records to estimate the runtime offset
        runtime2 = adc['adc_time'].iloc[-1] + (adc['runtime'].iloc[:n] - adc['adc_time'].iloc[:n]).median() - runtime_offset

        # if the difference between the two estimates is greater than 0.2 seconds, use the second one
        if abs(runtime - runtime2) > 0.2:
            runtime = runtime2
    else:
        return np.nan, np.nan, np.nan

    looktime = runtime - inhibittime
    ml_analyzed = FLOW_RATE * looktime / 60

    return ml_analyzed, looktime, runtime

def compute_ml_analyzed_s2(b):
    hdr_runtime = b.header('runtime')
    hdr_inhibittime = b.header('inhibittime')
    _, adc_looktime, adc_runtime = compute_ml_analyzed_s2_adc(b.adc)
    adc_inhibittime = adc_runtime - adc_looktime
    rat = hdr_runtime / adc_runtime
    if rat < 0.98 or rat > 1.02:
        runtime = adc_runtime
    else:
        runtime = hdr_runtime
    rat = hdr_inhibittime / adc_inhibittime
    if rat < 0.98 or rat > 1.02:
        inhibittime = adc_inhibittime
    else:
        inhibittime = hdr_inhibittime
    looktime = runtime - inhibittime
    ml_analyzed = FLOW_RATE * looktime / 60
    return ml_analyzed, looktime, runtime


def compute_ml_analyzed(b):
    s = b.schema
    if b.pid.instrument == 5 and b.timestamp >= pd.to_datetime('2015-06-01', utc=True):
        # IFCB5 bins after June 2015 require a non-default min_proc_time
        return compute_ml_analyzed_s1_adc(b.adc, min_proc_time=0.05)
    elif s is SCHEMA_VERSION_1:
        return compute_ml_analyzed_s1_adc(b.adc)
    elif s is SCHEMA_VERSION_2:
        return compute_ml_analyzed_s2(b)
    else: # unknown bin type, indicating some upstream error
        return np.nan, np.nan, np.nan