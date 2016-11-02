import unittest
import os
import shutil

from ...tests.utils import test_dir

from ..io import open_raw
from ..bins import BaseBin
from ..identifiers import Pid
from ..adc import SCHEMA

from .fileset_info import list_test_bins
from .bins import assert_bin_equals

class MockBin(BaseBin):
    def __init__(self, pid):
        self.pid = Pid(pid)

def test_schema_attrs(b):
    for attr in b.schema.__dict__:
        if attr[0] != '_':
            assert getattr(b, attr) == getattr(b.schema, attr)
            
class TestBaseBin(unittest.TestCase):
    def test_v1_schema_attrs(self):
        b = MockBin('IFCB1_2000_001_000000')
        assert b.schema == SCHEMA[1]
        test_schema_attrs(b)
    def test_v2_schema_attrs(self):
        b = MockBin('D20000101T000000_IFCB001')
        assert b.schema == SCHEMA[2]
        test_schema_attrs(b)

class TestMemoryBin(unittest.TestCase):
    def test_read_cmgr(self):
        for a in list_test_bins():
            with a:
                b = a.read()
            assert_bin_equals(a, b)
    def test_read(self):
        for a in list_test_bins():
            b = a.read()
            assert_bin_equals(a, b)
    def test_read_del(self):
        for a in list_test_bins():
            with test_dir() as d:
                shutil.copy(a.fileset.adc_path, d)
                shutil.copy(a.fileset.roi_path, d)
                shutil.copy(a.fileset.hdr_path, d)
                p = os.path.join(d, os.path.basename(a.fileset.adc_path))
                with open_raw(p) as b:
                    c = b.read()
            assert_bin_equals(a, c)
