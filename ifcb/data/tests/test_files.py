import unittest
import os
import sys

import numpy as np

from ifcb.data import files

TEST_DATA_DIR=os.path.join('ifcb','data','tests','data')

TEST_LIDS = [
    'D20130526T095207_IFCB013',
    'IFCB5_2012_028_081515'
]

WHITELIST = ['data','white']

def data_dir():
    for p in sys.path:
        fp = os.path.join(p, TEST_DATA_DIR)
        if os.path.exists(fp):
            return fp
    raise KeyError('cannot find %s on sys.path' % TEST_DATA_DIR)

class TestFiles(unittest.TestCase):
    def setUp(self):
        self.data_dir = data_dir()
    def test_list_data_dirs(self):
        for dd in files.list_data_dirs(self.data_dir):
            assert 'adc' in [f[-3:] for f in os.listdir(dd)]
    def test_data_directory(self):
        dd = files.DataDirectory(self.data_dir)
        fss = list(dd)
        assert len(fss) == 1 # only one whitelisted by default
        dd = files.DataDirectory(self.data_dir, whitelist=WHITELIST)
        fss = list(dd)
        assert len(fss) == 2 # including whitelisted one
        for fs in fss:
            assert fs.exists()
            assert os.path.exists(fs.adc_path)
            assert os.path.exists(fs.hdr_path)
            assert os.path.exists(fs.roi_path)
        lids = [fs.lid for fs in fss]
        for lid in TEST_LIDS:
            assert lid in lids
            assert lid in dd
        for fs in fss:
            assert dd[fs.lid].lid == fs.lid
    def test_list_filesets(self):
        """test with validation off and search"""
        paths = list(files.list_filesets(self.data_dir, whitelist=WHITELIST, validate=False))
        assert len(paths) == 3
