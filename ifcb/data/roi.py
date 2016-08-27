from itertools import izip
from functools32 import lru_cache

import numpy as np

import h5py as h5
from .adc import Adc
from .h5utils import open_h5_group

def read_image(inroi, byte_offset, width, height):
    """inroi is roi file open in random access mode"""
    length = width * height
    inroi.seek(byte_offset)
    return np.fromstring(inroi.read(length), dtype=np.uint8).reshape((width,height))

class Roi(object):
    def __init__(self, adc, roi_path):
        """parameters:
        adc - path of adc file, Adc object, or adc dataframe
        roi_path - path to roi file"""
        # duck type adc argument
        self._adc = None
        try:
            self._adc = adc.to_dataframe()
        except AttributeError:
            pass
        try:
            if self._adc is None:
                self.adc = Adc(adc).to_dataframe()
        except:
            pass
        try:
            if self._adc is None:
                adc.columns # ersatz type test for DataFrame
                self._adc = adc
        except AttributeError:
            raise ValueError('adc parameter type not supported')
        # now remove 0x0 rois from adc data
        self._adc = self._adc[self._adc['width'] != 0]
        self.path = roi_path
        self._inroi = None # open roi file
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
    @property
    def index(self):
        return self._adc.index
    @lru_cache(maxsize=2)
    def get_image(self, roi_number):
        roi_number = int(roi_number)
        keys = ['byteOffset', 'width', 'height']
        try:
            bo, width, height = [self._adc[k][roi_number] for k in keys]
        except KeyError:
            raise KeyError('adc data does not contain a roi #%d' % roi_number)
        if width * height == 0:
            raise KeyError('roi #%d is 0x0' % roi_number)
        if self._inroi is not None:
            return read_image(self._inroi, bo, width, height)
        else:
            with open(self.path,'rb') as inroi:
                return read_image(inroi, bo, width, height)
    def __len__(self):
        return len(self._adc)
    @property
    def index(self):
        return self._adc.index
    def __iter__(self):
        def iter():
            for roi_number in self.index:
                yield self.get_image(roi_number)
        if not self.isopen():
            with self as me:
                for im in iter():
                    yield im
        else:
            for im in iter():
                yield im
    def __getitem__(self, roi_number):
        """wraps get_image"""
        return self.get_image(roi_number)
    def to_hdf(self, hdf_file, group_path=None, replace=True, **kw):
        with open_h5_group(hdf_file, group_path, replace=replace) as g:
            g.attrs['index'] = self.index
            for roi_number, image in izip(self.index, self):
                key = str(roi_number)
                g.create_dataset(key, data=image)
    def __repr__(self):
        return '<ROI %s>' % self.path
    def __str__(self):
        return self.path








