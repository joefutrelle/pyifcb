from itertools import izip
from functools32 import lru_cache

import numpy as np

from .adc import AdcFile

def read_image(inroi, byte_offset, width, height):
    """inroi is roi file open in random access mode"""
    length = width * height
    inroi.seek(byte_offset)
    return np.fromstring(inroi.read(length), dtype=np.uint8).reshape((width,height))

class RoiFile(object):
    def __init__(self, adc, roi_path):
        """parameters:
        adc - path of adc file, Adc object
        roi_path - path to roi file"""
        # duck type adc argument
        self.adc = None
        try:
            adc.pid # should work for AdcFile objects
            self.adc = adc
        except AttributeError:
            self.adc = AdcFile(adc)
        # now remove 0x0 rois from adc data
        csv = self.adc.csv
        s = self.adc.schema
        csv = csv[csv[s.ROI_WIDTH] != 0]
        self.csv = csv
        self.path = roi_path
        self._inroi = None # for the open roi file
    def isopen(self):
        return self._inroi is not None
    def open(self, reopen=True):
        # close if already open
        if self.isopen():
            if reopen:
                self.close()
            else:
                return self
        self._inroi = open(self.path, 'rb')
        return self
    def close(self):
        self._inroi.close()
        self._inroi = None
    def __enter__(self, reopen=True):
        self.open(reopen=reopen)
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    @lru_cache(maxsize=2)
    def get_image(self, roi_number):
        roi_number = int(roi_number)
        s = self.adc.schema
        keys = [s.START_BYTE, s.ROI_WIDTH, s.ROI_HEIGHT]
        try:
            bo, width, height = [self.csv[k][roi_number] for k in keys]
        except KeyError:
            raise # FIXME
            raise KeyError('adc data does not contain a roi #%d' % roi_number)
        if width * height == 0:
            raise KeyError('roi #%d is 0x0' % roi_number)
        if self._inroi is not None:
            return read_image(self._inroi, bo, height, width)
        else:
            with open(self.path,'rb') as inroi:
                return read_image(inroi, bo, height, width)
    def __len__(self):
        return len(self.csv)
    @property
    def index(self):
        return self.csv.index
    def keys(self):
        return list(self.index)
    def __iter__(self):
        return iter(self.keys())
    def iteritems(self):
        if not self.isopen():
            with self:
                for i in self:
                    yield i, self[i]
        else:
            for i in self:
                yield i, self[i]
    def items(self):
        """warning: contains all image data, which can use
        very large amounts of RAM"""
        return list(self.iteritems())
    def __contains__(self, roi_number):
        return roi_number in self.keys()
    def __getitem__(self, roi_number):
        """wraps get_image"""
        return self.get_image(roi_number)
    def to_dict(self):
        """warning: contains all image data, which can use
        very large amounts of RAM"""
        return dict(self.items())
    def to_hdf(self, hdf_file, group=None, replace=True):
        from .hdf import roi2hdf
        roi2hdf(self, hdf_file, group, replace=replace)
    def __repr__(self):
        return '<ROI file %s>' % self.path
    def __str__(self):
        return self.path








