import pandas as pd
import h5py as h5
from oii.utils import imemoize

from .h5utils import df2h5, touch_group
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
            self.parsed
    @property
    @imemoize
    def parsed(self):
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
        return self.parsed
    def to_dict(self):
        return self.parsed.to_dict('series')
    def to_hdf(self, hdf_file, group_path='adc', replace=True, compression='gzip'):
        def write_df(f):
            g = touch_group(f, group_path)
            df2h5(g, self.parsed, compression=compression, replace=replace)
        try:
            write_df(hdf_file)
        except:
            mode = 'w' if replace else 'a'
            with h5.File(hdf_file,mode) as f:
                write_df(f)
    def __repr__(self):
        return '<ADC %s>' % self.path
    def __str__(self):
        return self.path
