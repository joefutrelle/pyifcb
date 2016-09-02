import os

import pandas as pd
import h5py as h5
from functools32 import lru_cache

from .identifiers import Pid
from .bins import BaseDictlike

# column names by schema
# FIXME these are not anywhere in raw data except new-style instruments contain
# an attribute listing column names
"""
COLUMNS = {
    1: 'trigger processingEndTime fluorescenceLow fluoresenceHigh scatteringLow scatteringHigh comparatorPulse triggerOpenTime frameGrabTime bottom left height width byteOffset valveStatus'.split(' '),
    2: 'trigger processingEndTime pmtA pmtB pmtC pmtD peakA peakB peakC peakD timeOfFlight grabTimeStart frameGrabTime bottom left height width byteOffset comparatorOut startPoint signalStrength valveStatus'.split(' ')
}
"""

class SCHEMA_VERSION_1(object):
    name = 'v1'
    TRIGGER = 0
    ROI_X = 9
    ROI_Y = 10
    ROI_WIDTH = 11
    ROI_HEIGHT = 12
    START_BYTE = 13

class SCHEMA_VERSION_2(object):
    name = 'v2'
    TRIGGER = 0
    ROI_X = 13
    ROI_Y = 14
    ROI_WIDTH = 15
    ROI_HEIGHT = 16
    START_BYTE = 17

SCHEMA = {
    1: SCHEMA_VERSION_1,
    2: SCHEMA_VERSION_2,
    SCHEMA_VERSION_1.name: SCHEMA_VERSION_1,
    SCHEMA_VERSION_2.name: SCHEMA_VERSION_2
}

class AdcFile(BaseDictlike):
    def __init__(self, adc_path, parse=False):
        self.path = adc_path
        self.pid = Pid(adc_path)
        self.schema_version = self.pid.schema_version
        self.schema = SCHEMA[self.schema_version]
        if parse:
            self.csv
    @property
    @lru_cache()
    def csv(self):
        df = pd.read_csv(self.path, header=None, index_col=False)
        df.index += 1 # index by 1-based ROI number
        return df
    def to_dataframe(self):
        return self.csv
    def to_dict(self):
        return self.csv.to_dict('series')
    def to_hdf(self, hdf_file, group=None, replace=True, **kw):
        """
        parameters:
        hdf_file - hdf file pathname, or h5.File or h5.Group
        group - optional (sub)group path
        replace - for files, whether or not to replace file
        """
        from .hdf import adc2hdf
        adc2hdf(self, hdf_file, group, replace=replace, **kw)
    def iterkeys(self):
        for k in self.csv.index:
            yield k
    @lru_cache()
    def get_target(self, target_number):
        d = tuple(self.csv[c][target_number] for c in self.csv.columns)
        return d
    def __getitem__(self, target_number):
        return self.get_target(target_number)
    def __repr__(self):
        return '<ADC file %s>' % self.path
    def __str__(self):
        return self.path
