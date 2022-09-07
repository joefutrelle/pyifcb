import unittest

import numpy as np

from ifcb.data.files import DataDirectory, FilesetBin
from ifcb.data.stitching import Stitcher, InfilledImages

from .fileset_info import TEST_FILES, TEST_DATA_DIR

class TestStitcher(unittest.TestCase):
    @unittest.skip('deprecated use of numpy indexing in test code')
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
    def test_infill_values(self):
        dd = DataDirectory(TEST_DATA_DIR)
        for lid, tf in TEST_FILES.items():
            if 'roi_numbers_stitched' in tf:
                b = dd[lid]
                rns = tf['roi_numbers_stitched']
                roi_corners = tf['stitched_corners']
                iis = InfilledImages(b)
                for rn in rns:
                    ii = iis[rn]
                    c1 = ii[0,0]
                    c2 = ii[0,-1]
                    c3 = ii[-1,0]
                    c4 = ii[-1,-1]
                    corners = [c1, c2, c3, c4]
                    assert roi_corners[rn] == corners

        
