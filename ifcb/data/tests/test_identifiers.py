import unittest
import random

from .. import identifiers as ids
from ..identifiers import Pid

"""
ways to mess up an identifier:

* insert any character anywhere
* delete any character anywhere
* change any letter to a letter other than 'D', 'T', 'I', 'F', 'C', or 'B'

"""

GOOD_V1 = 'IFCB1_2000_001_123456'
GOOD_V2 = 'D20000101T123456_IFCB001'

GOOD = [GOOD_V1, GOOD_V2]

ALPHA = 'IFCBDTXYZ'
CHARS = '0123456789_' + ALPHA

class DestroyPid(object):
    def __init__(self, pid):
        self.pid = pid
    def insert_character(self):
        for d in CHARS:
            for i in range(len(self.pid)+1):
                yield self.pid[:i] + d + self.pid[i:]
    def delete_character(self):
        for i in range(len(self.pid)):
            yield self.pid[:i] + self.pid[i+1:]
    def mod_letter(self):
        for i in range(len(self.pid)):
            pc = self.pid[i]
            if pc not in ALPHA:
                continue
            for c in ALPHA:
                if c == pc: continue
                yield self.pid[:i] + c + self.pid[i+1:]
                
class TestIdentifiers(unittest.TestCase):
    def test_schema_version(self):
        assert Pid(GOOD_V1).schema_version == 1, 'expected schema version 1'
        assert Pid(GOOD_V2).schema_version == 2, 'expected schema version 2'
    def test_unparse(self):
        for pid in GOOD:
            assert ids.unparse(Pid(pid).parsed) == pid
    def test_timestamp(self):
        for pid in GOOD:
            dt = Pid(pid).timestamp
            assert dt.year == 2000, 'year wrong'
            assert dt.month == 1, 'month wrong'
            assert dt.day == 1, 'day wrong'
            assert dt.hour == 12, 'hour wrong'
            assert dt.minute == 34, 'minute wrong'
            assert dt.second == 56, 'second wrong'
    def test_target(self):
        target = 123
        target_string = '%05d' % target
        for pid in GOOD:
            target_pid = '%s_%s' % (pid, target_string)
            assert Pid(target_pid).target == target, 'target wrong'
    def test_destroy(self):
        for pid in GOOD:
            d = DestroyPid(pid)
            for p in d.insert_character():
                with self.assertRaises(ValueError):
                    Pid(p).parsed
            for p in d.delete_character():
                with self.assertRaises(ValueError):
                    Pid(p).parsed
            for p in d.mod_letter():
                with self.assertRaises(ValueError):
                    Pid(p).parsed

class TestV1Identifiers(unittest.TestCase):
    def test_timestamp_validation(self):
        with self.assertRaises(ValueError):
            ids.parse('IFCB1_2000_999_000000')
        with self.assertRaises(ValueError):
            ids.parse('IFCB1_2000_001_990000')
        with self.assertRaises(ValueError):
            ids.parse('IFCB1_2000_001_009900')
        with self.assertRaises(ValueError):
            ids.parse('IFCB1_2000_001_000099')
    def test_instrument(self):
        assert Pid(GOOD_V1).instrument == 1

class TestV2Identifiers(unittest.TestCase):
    def test_timestamp_validation(self):
        with self.assertRaises(ValueError):
            ids.parse('D20009901T000000_IFCB001')
        with self.assertRaises(ValueError):
            ids.parse('D20000199T000000_IFCB001')
        with self.assertRaises(ValueError):
            ids.parse('D20000101T990000_IFCB001')
        with self.assertRaises(ValueError):
            ids.parse('D20000101T009900_IFCB001')
        with self.assertRaises(ValueError):
            ids.parse('D20000101T000099_IFCB001')
    def test_instrument(self):
        assert Pid(GOOD_V2).instrument == 1
