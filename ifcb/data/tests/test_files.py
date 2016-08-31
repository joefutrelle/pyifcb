import unittest
import os
import sys

import numpy as np

from ifcb.data import files

TEST_DATA_DIR='ifcb/data/tests/data'

def data_dir():
    for p in sys.path:
        fp = os.path.join(p, TEST_DATA_DIR)
        if os.path.exists(fp):
            return fp
    raise KeyError('cannot find %s on sys.path' % TEST_DATA_DIR)

class TestFiles(unittest.TestCase):
    def test_data_dir(self):
        dd = files.DataDirectory(data_dir())
        fss = list(dd)
        assert len(fss) == 2
        for fs in fss:
            assert fs.exists()
            assert os.path.exists(fs.adc_path)
            assert os.path.exists(fs.hdr_path)
            assert os.path.exists(fs.roi_path)
