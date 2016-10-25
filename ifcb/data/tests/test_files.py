import unittest
import os
import sys

import numpy as np

from .. import files
from .fileset_info import TEST_FILES, data_dir, WHITELIST, list_test_filesets

class TestListUtils(unittest.TestCase):
    def setUp(self):
        self.data_dir = data_dir()
    def test_list_data_dirs(self):
        for dd in files.list_data_dirs(self.data_dir):
            assert 'adc' in [f[-3:] for f in os.listdir(dd)]
    def test_list_data_dirs_prune(self):
        for dd in files.list_data_dirs(self.data_dir):
            for n in os.listdir(dd):
                assert 'decoy.adc' not in n
    def test_list_data_dirs_no_prune(self):
        for dd in files.list_data_dirs(self.data_dir, prune=False):
            for n in os.listdir(dd):
                if 'decoy.adc' in n:
                    return
        raise ValueError('decoy not found with prune=False')
    def test_list_filesets(self):
        """test with validation off and search"""
        paths = list(files.list_filesets(self.data_dir, whitelist=WHITELIST, validate=False))
        assert len(paths) == 3

class TestDataDirectory(unittest.TestCase):
    def setUp(self):
        self.data_dir = data_dir()
        self.default = files.DataDirectory(self.data_dir)
        self.whitelist = files.DataDirectory(self.data_dir, whitelist=WHITELIST)
        self.blacklist = files.DataDirectory(self.data_dir, blacklist=['skip','invalid'])
    def test_iteration(self):
        fss = list(self.default)
        assert len(fss) == 1 # only one whitelisted by default
        fss = list(self.whitelist)
        assert len(fss) == 2 # including whitelisted one
    def test_exists(self):
        fss = [b.fileset for b in self.whitelist]
        for fs in fss:
            assert fs.exists()
            assert os.path.exists(fs.adc_path)
            assert os.path.exists(fs.hdr_path)
            assert os.path.exists(fs.roi_path)
    def test_lids(self):
        fss = [b.fileset for b in self.whitelist]
        lids = [fs.lid for fs in fss]
        for lid in TEST_FILES:
            assert lid in lids
        for fs in fss:
            assert self.whitelist[fs.lid].lid == fs.lid
    def test_getsizes(self):
        for fs in list_test_filesets():
            sizes = TEST_FILES[fs.lid]['sizes']
            assert fs.getsizes() == sizes
            assert fs.getsize() == sum(sizes.values())
    def test_descendants(self):
        assert len(list(self.default.list_descendants())) == 3
        assert len(list(self.blacklist.list_descendants())) == 2

        
