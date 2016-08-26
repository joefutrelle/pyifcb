from functools32 import lru_cache

import numpy as np

from .adc import Adc

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
        self.roi_path = roi_path
    @lru_cache(maxsize=2)
    def get_image(self, roi_number):
        keys = ['byteOffset', 'width', 'height']
        try:
            bo, width, height = [self._adc[k][roi_number] for k in keys]
        except KeyError:
            raise KeyError('adc data does not contain a roi #%d' % roi_number)
        length = width * height
        if length == 0:
            raise KeyError('roi #%d is 0x0' % roi_number)
        with open(self.roi_path,'rb') as inroi:
            inroi.seek(bo)
            im = np.fromstring(inroi.read(length), dtype=np.uint8).reshape((width,height))
            return im
    def __len__(self):
        return len(self._adc)
    @property
    def index(self):
        return self._adc.index
    def __iter__(self):
        for roi_number in self.index:
            yield self[roi_number]
    def __getitem__(self, roi_number):
        """wraps get_image"""
        return self.get_image(roi_number)
                

                
