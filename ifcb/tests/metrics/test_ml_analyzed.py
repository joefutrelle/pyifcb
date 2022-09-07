import unittest

import numpy as np

from ifcb.tests.data.fileset_info import list_test_bins, get_fileset_bin

from ifcb.metrics.ml_analyzed import compute_ml_analyzed

TARGET_ML_ANALYZED = {
    'IFCB5_2012_028_081515': (0.003391470833333334, 0.8139530000000001, 1.251953),
    'D20130526T095207_IFCB013': (4.8850699041666665, 1172.416777, 1184.037103)
}

class TestMlAnalyzed(unittest.TestCase):
    def test_ml_analyzed(self):
        for b in list_test_bins():
            result = compute_ml_analyzed(b)
            target_result = TARGET_ML_ANALYZED[b.lid]
            for rv, trv in zip(result, target_result):
                assert np.isclose(rv, trv)
