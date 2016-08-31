import unittest
import sys
from contextlib import contextmanager

import numpy as np

from .fileset_info import TEST_FILES, list_test_filesets

class TestRoi(unittest.TestCase):
    def setUp(self):
        self.data = { fs.lid: fs for fs in list_test_filesets() }
    def fsinfo(self):
        for lid, info in TEST_FILES.items():
            fs = self.data[lid]
            yield lid, info, fs
    def test_images(self):
        for lid, info, fs in self.fsinfo():
            assert len(fs.roi) == info['n_rois']
            image = fs.roi[info['roi_number']]
            assert image.shape == info['roi_shape']
            A = info['roi_slice']
            B = image[:5,:5] # small slice
            assert np.all(A == B)
    def test_with(self):
        for lid, info, fs in self.fsinfo():
            assert not fs.roi.isopen()
            with fs.roi as o:
                assert o.isopen()
                assert fs.roi.isopen()
            assert not fs.roi.isopen()
    def test_dictlike(self):
        for lid, info, fs in self.fsinfo():
            rn = info['roi_numbers']
            assert set(fs.roi.keys()) == set(rn)
            for n in rn:
                assert n in fs.roi
            no = 0
            assert no not in fs.roi

