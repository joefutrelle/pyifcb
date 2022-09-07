import numpy as np
import pandas as pd

import scipy.stats as stats

from ifcb.data.adc import SCHEMA_VERSION_1, SCHEMA_VERSION_2


def read_ml_analyzed(path):
    """read from the legacy matlab files"""
    from scipy.io import loadmat
    mat = loadmat(path, squeeze_me=True)
    # ignore variables other than the following
    cols = ['filelist_all', 'looktime', 'minproctime', 'ml_analyzed', 'runtime']
    # convert to dataframe
    df = pd.DataFrame({ c: mat[c] for c in cols }, columns=cols)
    df.index = df.pop('filelist_all') # index by bin LID
    return df

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

def compute_ml_analyzed_s1(abin, min_proc_time=0.073):
    return compute_ml_analyzed_s1_adc(abin.adc, min_proc_time=min_proc_time)

def compute_ml_analyzed_s2_adc(abin):
    """compute ml_analyzed for a new instrument, based on ADC file"""
    FLOW_RATE = 0.25 # ml/minute
    s = abin.schema
    adc = abin.adc
    def ma(row):
        run_time = row[s.RUN_TIME]
        inhibit_time = row[s.INHIBIT_TIME]
        look_time = run_time - inhibit_time
        ml_analyzed = FLOW_RATE * (look_time / 60.)
        return ml_analyzed, look_time, run_time
    last_row = adc.iloc[-1]
    ml_analyzed, look_time, run_time = ma(last_row)
    if ml_analyzed <= 0 or abs(last_row[s.RUN_TIME] - last_row[s.ADC_TIME]) >= 0.3:
        row = adc.iloc[-2]
        ml_analyzed, look_time, run_time = ma(row)
    if ml_analyzed <= 0:
        row = adc.iloc[-2]
        run_time = row[s.ADC_TIME]
        nz = adc[s.RUN_TIME].to_numpy().nonzero()[0]
        mode_inhibit_time = stats.mode(np.diff(adc[s.INHIBIT_TIME].iloc[nz]))[0][0]
        last_good_inhibit_time = adc[s.INHIBIT_TIME].iloc[nz[-1]]
        inhibit_time = last_good_inhibit_time + (len(adc) - len(nz)) * mode_inhibit_time
        look_time = run_time - inhibit_time
        ml_analyzed = FLOW_RATE * (look_time / 60)
    return ml_analyzed, look_time, run_time

def compute_ml_analyzed_s2(abin):
    """compute ml_analyzed for a new instrument"""
    FLOW_RATE = 0.25 # ml/minute
    # ml analyzed is (run time - inhibit time) * flow rate
    run_time = abin.header('runTime')
    inhibit_time = abin.header('inhibitTime')
    look_time = run_time - inhibit_time
    ml_analyzed = FLOW_RATE * (look_time / 60.)
    if look_time > 0:
        return ml_analyzed, look_time, run_time
    else:
        return compute_ml_analyzed_s2_adc(abin)

def compute_ml_analyzed(abin):
    """returns ml_analyzed, look time, run time"""
    s = abin.schema
    if abin.pid.instrument == 5 and abin.timestamp >= pd.to_datetime('2015-06-01', utc=True):
        # IFCB5 bins after June 2015 require a non-default min_proc_time
        return compute_ml_analyzed_s1(abin, min_proc_time=0.05)
    elif s is SCHEMA_VERSION_1:
        return compute_ml_analyzed_s1(abin)
    elif s is SCHEMA_VERSION_2:
        return compute_ml_analyzed_s2(abin)
    else: # unknown bin type, indicating some upstream error
        return np.nan, np.nan, np.nan
