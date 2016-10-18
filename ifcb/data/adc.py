"""
Support for parsing and accessing IFCB ADC data.
"""

import os

import pandas as pd
import h5py as h5
from functools32 import lru_cache

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
    name = 'v1'
    TRIGGER = 0
    ROI_X = 9
    ROI_Y = 10
    ROI_WIDTH = 11
    ROI_HEIGHT = 12
    START_BYTE = 13

class SCHEMA_VERSION_2(object):
    """
    IFCB revision 2 schema.
    """
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
"""
IFCB schemas
"""

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
        :param parse: (optional) whether to parse the file
          (if not, parsing is deferred until data is accessed)
        """
        self.path = adc_path
        self.pid = Pid(adc_path)
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
        df = pd.read_csv(self.path, header=None, index_col=False)
        df.index += 1 # index by 1-based ROI number
        return df
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

        :param hdf_file: the root HDF
          object (h5.File or h5.Group) in which to write
          the ADC data
        :param group (optional): a path below the sub-group
          to use
        :param replace: whether to replace any existing data
          at that location in the HDF file
        """
        from .hdf import adc2hdf
        adc2hdf(self, hdf_file, group, replace=replace, **kw)
    def iterkeys(self):
        """
        Yield the target numbers of this ADC file, in order.
        """
        for k in self.csv.index:
            yield k
    def __len__(self):
        return len(self.csv)
    @lru_cache()
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
