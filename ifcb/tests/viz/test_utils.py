import unittest

import numpy as np

from ifcb.tests.data.fileset_info import get_fileset_bin

from ifcb.viz.utils import square_letterboxed, SQUARE_LETTERBOXED_DEFAULT_SIZE

SL_BIN_LID = 'IFCB5_2012_028_081515'

SL_MEDIAN = np.array([[205, 205, 205, 205, 205],
       [207, 204, 207, 205, 204],
       [206, 206, 211, 204, 205],
       [205, 205, 205, 205, 205],
       [205, 205, 205, 205, 205]])

SL_MEAN = np.array([[202, 202, 202, 202, 202],
       [207, 204, 207, 205, 204],
       [206, 206, 211, 204, 205],
       [202, 202, 202, 202, 202],
       [202, 202, 202, 202, 202]])

SL_27 = np.array([[ 27,  27,  27,  27,  27],
       [207, 204, 207, 205, 204],
       [206, 206, 211, 204, 205],
       [ 27,  27,  27,  27,  27],
       [ 27,  27,  27,  27,  27]])

class TestSquareLetterboxed(unittest.TestCase):
    def setUp(self):
        b = get_fileset_bin(SL_BIN_LID)
        self.img = b.images[1]
    def test_fill_value_median(self):
        sl = square_letterboxed(self.img, size=5)
        assert np.allclose(sl, SL_MEDIAN)
        sl = square_letterboxed(self.img, size=5, fill_value='median')
        assert np.allclose(sl, SL_MEDIAN)
    def test_fill_value_mean(self):
        sl = square_letterboxed(self.img, size=5, fill_value='mean')
        assert np.allclose(sl, SL_MEAN)
    def test_fill_value_27(self):
        sl = square_letterboxed(self.img, size=5, fill_value=27)
        assert np.allclose(sl, SL_27)
    def test_size(self):
        sl = square_letterboxed(self.img, size=20)
        assert sl.shape == (20, 20)
    def test_default_size(self):
        sl = square_letterboxed(self.img)
        assert sl.shape[0] == SQUARE_LETTERBOXED_DEFAULT_SIZE
        assert sl.shape[1] == SQUARE_LETTERBOXED_DEFAULT_SIZE