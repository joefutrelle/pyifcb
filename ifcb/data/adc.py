"""
Support for parsing and accessing IFCB ADC data.
"""

import os
from io import BytesIO

import pandas as pd
from pandas.errors import EmptyDataError

from functools import lru_cache

from .identifiers import Pid
from .utils import BaseDictlike

# column names by schema
# FIXME these are not anywhere in raw data except new-style instruments contain
# an attribute listing column names

#COLUMNS = {
#    1: 'trigger processingEndTime fluorescenceLow fluoresenceHigh scatteringLow scatteringHigh comparatorPulse triggerOpenTime frameGrabTime bottom left height width byteOffset valveStatus'.split(' '),
#    2: 'trigger processingEndTime pmtA pmtB pmtC pmtD peakA peakB peakC peakD timeOfFlight grabTimeStart frameGrabTime bottom left height width byteOffset comparatorOut startPoint signalStrength valveStatus'.split(' ')
#}


class SCHEMA_VERSION_1(object):
    """
    IFCB revision 1 schema.
    """
    _name = 'v1'
    _cols = range(15)
    TRIGGER = 0
    PROCESSING_END_TIME = 1
    FLUORESCENCE_LOW = 2
    FLUORESCENCE_HIGH = 3
    SCATTERING_LOW = 4
    SCATTERING_HIGH = 5
    COMPARATOR_PULSE = 6
    TRIGGER_OPEN_TIME = 7
    FRAME_GRAB_TIME = 8
    ROI_X = 9
    ROI_Y = 10
    ROI_WIDTH = 11
    ROI_HEIGHT = 12
    START_BYTE = 13
    VALVE_STATUS = 14

class SCHEMA_VERSION_2(object):
    """
    IFCB revision 2 schema.
    """
    _name = 'v2'
    _cols = range(24)
    TRIGGER = 0
    ADC_TIME = 1
    PMT_A = 2
    PMT_B = 3
    PMT_C = 4
    PMT_D = 5
    PEAK_A = 6
    PEAK_B = 7
    PEAK_C = 8
    PEAK_D = 9
    TIME_OF_FLIGHT = 10
    GRAB_TIME_START = 11
    GRAB_TIME_END = 12
    ROI_X = 13
    ROI_Y = 14
    ROI_WIDTH = 15
    ROI_HEIGHT = 16
    START_BYTE = 17
    COMPARATOR_OUT = 18
    START_POINT = 19
    SIGNAL_LENGTH = 20
    STATUS = 21
    RUN_TIME = 22
    INHIBIT_TIME = 23

SCHEMA = {
    1: SCHEMA_VERSION_1,
    2: SCHEMA_VERSION_2,
    SCHEMA_VERSION_1._name: SCHEMA_VERSION_1,
    SCHEMA_VERSION_2._name: SCHEMA_VERSION_2
}

def schema_names(schema):
    return [v.lower() for v in vars(schema) if not v.startswith('_')]

"""
IFCB schemas
"""

def parse_adc_file(adc_file):
    """
    Parse an ADC file and return it as a Pandas
    DataFrame, indexed by target number.

    :param adc_file: the pathname or URL of the ADC file,
      or a buffer containing the ADC data
    """
    try:
        df = pd.read_csv(adc_file, header=None, index_col=False)
        df.index += 1 # index by 1-based ROI number
        return df
    except EmptyDataError:
        s = SCHEMA[Pid(adc_file).schema_version]
        cols = s._cols
        return pd.DataFrame({c:[] for c in cols}, columns=cols)
    
class AdcFile(BaseDictlike):
    """
    Represents an IFCB ``.adc`` file.

    Provides a dict-like interface; keys are target numbers,
    values are target records. Target records are tuples which
    are indexed according to values in the associated schema
    (accessible via the ``schema`` property).

    :Example:

    >>> adc = AdcFile('IFCB4_2013_007_123423.adc')
    >>> adc[23][adc.schema.ROI_WIDTH]
    135

    """
    def __init__(self, adc_path, parse=False):
        """
        :param adc_path: the path of the ``.adc`` file.
        :param parse: whether to parse the file
          (if not, parsing is deferred until data is accessed)
        """
        self.path = adc_path
        self.pid = Pid(adc_path, parse=parse)
        self.schema_version = self.pid.schema_version
        self.schema = SCHEMA[self.schema_version]
        if parse:
            self.csv
    def getsize(self):
        """
        :return int: the size of the file
        """
        return os.path.getsize(self.path)
    @property
    def lid(self):
        """
        The bin's LID
        """
        return self.pid.lid
    @property
    @lru_cache()
    def csv(self):
        """
        The underlying CSV data as a ``pandas.DataFrame``
        """
        return parse_adc_file(self.path)
    def to_dataframe(self):
        """
        Return the ADC data as a ``pandas.DataFrame``. If the
        file has not been parsed yet, this opens the file, parses it,
        and closes it.
        """
        return self.csv
    def to_dict(self):
        """
        Return the ADC data as a dictionary
        """
        return self.csv.to_dict('series')
    def to_hdf(self, hdf_file, group=None, replace=True, **kw):
        """
        Write the ADC file to an HDF file or group.

        :param hdf_file: the root HDF file pathname or
          object (h5py.File or h5py.Group) in which to write
          the ADC data
        :param group: a path below the sub-group
          to use
        :param replace: whether to replace any existing data
          at that location in the HDF file
        """
        from .hdf import adc2hdf
        adc2hdf(self, hdf_file, group, replace=replace, **kw)
    def keys(self):
        """
        Yield the target numbers of this ADC file, in order.
        """
        yield from self.csv.index
    def has_key(self, k):
        return k in self.csv.index
    def __len__(self):
        return len(self.csv)
    def get_target(self, target_number):
        """
        Get the ADC data for a given target, as a tuple.
        """
        d = tuple(self.csv[c][target_number] for c in self.csv.columns)
        return d
    def __getitem__(self, target_number):
        return self.get_target(target_number)
    def __repr__(self):
        return '<ADC file %s>' % self.path
    def __str__(self):
        return self.path

class AdcFragment(AdcFile):
    """
    Represents a specific range of targets in an ADC file.
    Skips parsing other lines from the ADC file, for performance
    reasons.
    """
    def __init__(self, adc_path, start=1, end=None, parse=False):
        self.start = start
        self.end = end
        super(AdcFragment, self).__init__(adc_path, parse=parse)
    @property
    def csv(self):
        with open(self.path) as adc_file:
            n, buf = 1, BytesIO()
            for line in adc_file:
                if n >= self.start:
                    buf.write(line.encode('utf8'))
                n += 1
                if n == self.end:
                    break
        buf.seek(0)
        df = pd.read_csv(buf, header=None, index_col=False)
        df.index += self.start # index by 1-based ROI number
        return df

