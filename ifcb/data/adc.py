import pandas as pd

from .identifiers import Pid

# columns by schema
COLUMNS = {
    1: 'trigger processingEndTime fluorescenceLow fluoresenceHigh scatteringLow scatteringHigh comparatorPulse triggerOpenTime frameGrabTime bottom left height width byteOffset valveStatus'.split(' '),
    2: 'trigger processingEndTime pmtA pmtB pmtC pmtD peakA peakB peakC peakD timeOfFlight grabTimeStart frameGrabTime bottom left height width byteOffset comparatorOut startPoint signalStrength valveStatus'.split(' ')
}

class Adc(object):
    def __init__(self, adc_path):
        self.path = adc_path
        self.pid = Pid(adc_path, parse=False)
    def parse(self):
        schema = COLUMNS[self.pid.schema_version]
        df = pd.read_csv(self.path, index_col=False)
        # deal with files that don't match the hardcoded schema
        cols = list(df.columns)
        if len(cols) > len(schema):
            cols[:len(schema)] = schema
        elif len(cols) < len(schema):
            cols = schema[:len(cols)]
        df.columns = cols
        return df
