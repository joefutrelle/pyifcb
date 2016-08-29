import os

import pandas as pd
import h5py as h5
from functools32 import lru_cache

from .h5utils import df2h5, open_h5_group
from .identifiers import Pid

# columns by schema
COLUMNS = {
    1: 'trigger processingEndTime fluorescenceLow fluoresenceHigh scatteringLow scatteringHigh comparatorPulse triggerOpenTime frameGrabTime bottom left height width byteOffset valveStatus'.split(' '),
    2: 'trigger processingEndTime pmtA pmtB pmtC pmtD peakA peakB peakC peakD timeOfFlight grabTimeStart frameGrabTime bottom left height width byteOffset comparatorOut startPoint signalStrength valveStatus'.split(' ')
}

class Adc(object):
    def __init__(self, adc_path, parse=False):
        self.path = adc_path
        self.pid = Pid(adc_path, parse=False)
        if parse:
            self.csv
    @property
    @lru_cache()
    def csv(self):
        schema = COLUMNS[self.pid.schema_version]
        df = pd.read_csv(self.path, header=None, index_col=False)
        # deal with files that don't match the hardcoded schema
        cols = list(df.columns)
        if len(cols) > len(schema):
            cols[:len(schema)] = schema
        elif len(cols) < len(schema):
            cols = schema[:len(cols)]
        df.columns = map(str,cols) # don't allow numeric column names
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
        with open_h5_group(hdf_file, group, replace=replace) as g:
            df2h5(g, self.csv, replace=replace, **kw)
    @lru_cache()
    def keys(self):
        return list(self.csv.index)
    def __len__(self):
        return len(self.csv)
    @lru_cache()
    def get_target(self, target_number):
        d = { c: self.csv[c][target_number] for c in self.csv.columns }
        d.update({ 'targetNumber': target_number })
        return d
    def __contains__(self, target_number):
        return target_number in self.csv.index
    def __getitem__(self, target_number):
        return self.get_target(target_number)
    def __iter__(self):
        return iter(self.csv.index)
    def iteritems(self):
        for i in self:
            yield i, self[i]
    def items(self):
        return list(self.iteritems())
    def __repr__(self):
        return '<ADC %s>' % self.path
    def __str__(self):
        return self.path
