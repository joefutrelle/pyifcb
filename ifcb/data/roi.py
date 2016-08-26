from functools32 import lru_cache

import numpy as np

from .adc import Adc

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
                adc.columns
                self._adc = adc
        except AttributeError:
            raise ValueError('adc parameter type not supported')
        # now remove 0x0 rois from adc data
        self._adc = self._adc[self._adc['width'] != 0]
        self.path = roi_path
        self._inroi = None # open roi file
    def __enter__(self):
        self._inroi = open(self.path,'rb')
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self._inroi.close()
        self._inroi = None
    @lru_cache(maxsize=2)
    def get_image(self, roi_number):
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
        for roi_number in self.index:
            yield self.get_image(roi_number)
    def __getitem__(self, roi_number):
        """wraps get_image"""
        return self.get_image(roi_number)
    def __repr__(self):
        return '<ROI %s>' % self.path
    def __str__(self):
        return self.path
                

                
