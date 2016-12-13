import unittest

import numpy as np

from ..files import DataDirectory, FilesetBin
from ..stitching import Stitcher, InfilledImages
from .fileset_info import TEST_FILES, TEST_DATA_DIR

class TestStitcher(unittest.TestCase):
    def test_stitched_size(self):
        dd = DataDirectory(TEST_DATA_DIR)
        for lid, tf in TEST_FILES.items():
            if 'stitched_roi_number' in tf: # does this have stitching data?
                b = dd[lid]
                s = Stitcher(b)
                target = tf['stitched_roi_number']
                coords = tf['stitched_roi_coords']
                assert target in s, 'stitched target missing'
                assert s[target].shape == tf['stitched_roi_shape'], 'stitched roi shape wrong'
                assert np.all(s[target][coords] == tf['stitched_roi_slice']), 'stitched roi data wrong'
    def test_infilled_keys(self):
        dd = DataDirectory(TEST_DATA_DIR)
        for lid, tf in TEST_FILES.items():
            if 'roi_numbers_stitched' in tf:
                b = dd[lid]
                rns = tf['roi_numbers_stitched']
                ii = InfilledImages(b)
                assert set(rns) == set(ii.keys())
