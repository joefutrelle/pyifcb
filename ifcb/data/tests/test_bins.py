import unittest

from ..bins import BaseBin
from ..identifiers import Pid
from ..adc import SCHEMA

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
