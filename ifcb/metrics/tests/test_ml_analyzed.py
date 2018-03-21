import unittest

from ifcb.data.tests.fileset_info import list_test_bins, get_fileset_bin

from ..ml_analyzed import compute_ml_analyzed

TARGET_ML_ANALYZED = {
    'IFCB5_2012_028_081515': (0.003391470833333334, 0.8139530000000001, 1.251953),
    'D20130526T095207_IFCB013': (5.080841170833334, 1219.401881, 1231.024861)
}

class TestMlAnalyzed(unittest.TestCase):
    def test_ml_analyzed(self):
        ma = { b.lid: compute_ml_analyzed(b) for b in list_test_bins() }
        for lid, result in ma.items():
            target_result = TARGET_ML_ANALYZED[lid]
            assert result == target_result
