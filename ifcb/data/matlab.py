import numpy as np
from scipy.io import savemat, loadmat
import pandas as pd

from .utils import BaseDictlike
from .bins import BaseBin

from .identifiers import Pid

PID_VAR = 'pid'
ADC_VAR = 'adc'
ROI_NUMBERS_VAR = 'roi_numbers'
IMAGES_VAR = 'images'
HEADERS_VAR = 'headers'

MAX_FIELD_LENGTH = 31

# notes about MATLAB format
# the matrix of ADC data is of a uniform type, so int columns
# come back as floats.

def bin2mat(b, mat_path):
    # ADC data
    adc = np.array(b.adc)
    # warning: reads all images into memory
    roi_numbers = sorted(b.images)
    images = [ b.images[r] for r in roi_numbers ]
    savemat(mat_path, {
        PID_VAR: str(b.lid), # remove non-bin parts of pid
        HEADERS_VAR: b.headers,
        ADC_VAR: adc,
        ROI_NUMBERS_VAR: roi_numbers,
        IMAGES_VAR: images
    }, long_field_names=True)

class _MatBinImages(BaseDictlike):
    def __init__(self, mat):
        self._mat = mat
    def keys(self):
        for k in self._mat[ROI_NUMBERS_VAR]:
            yield k
    def has_key(self, k):
        return k in self._mat[ROI_NUMBERS_VAR]
    def __getitem__(self, roi_number):
        i = 0
        for k in self.keys():
            if k == roi_number:
                return self._mat[IMAGES_VAR][i]
            i += 1 
        raise KeyError('no ROI #%d' % roi_number)
    
class MatBin(BaseBin):
    def __init__(self, mat_path):
        self._mat = loadmat(mat_path, squeeze_me=True)
        self.pid = Pid(self._mat[PID_VAR])
        self.adc = pd.DataFrame(self._mat[ADC_VAR]);
        self.adc.index += 1 # 1-based indexes
        self.images = _MatBinImages(self._mat)
        rec = self._mat[HEADERS_VAR]
        rec_names = rec.dtype.names
        self.headers = { n : np.asscalar(rec[n]) for n in rec_names }



