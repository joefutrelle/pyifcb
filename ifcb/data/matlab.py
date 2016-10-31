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
HEADER_NAMES_VAR = 'header_names'
HEADERS_VAR = 'headers'

MAX_FIELD_LENGTH = 31

# notes about MATLAB format
# the matrix of ADC data is of a uniform type, so int columns
# come back as floats.
# the max field name length for structs is 31 characters (at
# least in scipy.io), so field names in the struct are truncated
# to that max length.
# a separate list of field names is stored in the .mat file.
# that is right-space-padded upon reading, so the padding is
# stripped.

def bin2mat(b, mat_path):
    # ADC data
    adc = np.array(b.adc)
    # warning: reads all images into memory
    roi_numbers = sorted(b.images)
    images = [b.images[r] for r in roi_numbers]
    headers = { k[:MAX_FIELD_LENGTH]: v for k,v in b.headers.items() }
    savemat(mat_path, {
        PID_VAR: str(b.lid), # remove non-bin parts of pid
        HEADER_NAMES_VAR: sorted(b.headers.keys()),
        HEADERS_VAR: headers,
        ADC_VAR: adc,
        ROI_NUMBERS_VAR: roi_numbers,
        IMAGES_VAR: images
    })

class _MatBinImages(BaseDictlike):
    def __init__(self, mat):
        self._mat = mat
    def iterkeys(self):
        for k in self._mat[ROI_NUMBERS_VAR]:
            yield k
    def keys(self):
        return list(self._mat[ROI_NUMBERS_VAR])
    def has_key(self, k):
        return k in self._mat[ROI_NUMBERS_VAR]
    def __getitem__(self, roi_number):
        i = 0
        for k in self.iterkeys():
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
        _headers = self._mat[HEADERS_VAR]
        _names = [ n.rstrip(' ') for n in self._mat[HEADER_NAMES_VAR] ]
        self.headers = { n: _headers[n[:MAX_FIELD_LENGTH]] for n in _names }
