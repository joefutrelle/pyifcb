import unittest

import numpy as np

from ifcb.tests.data.fileset_info import list_test_bins

from ifcb.viz.mosaic import Mosaic

PACKED = {
    'IFCB5_2012_028_081515': {
        'y': [0, 0, 137, 182, 182],
        'x': [0, 238, 0, 0, 105],
        'roi_number': [2, 3, 6, 5, 1]
    },
    'D20130526T095207_IFCB013': {
        'y': [0, 89, 171, 237, 295, 337, 403, 453, 494, 237, 171, 337, 379, 527, 453, 527, 561, 561, 595],
        'x': [0, 0, 0, 0, 0, 0, 0, 0, 0, 112, 104, 96, 96, 0, 112, 88, 0, 72, 0],
        'roi_number': [114, 61, 11, 78, 47, 73, 66, 21, 54, 49, 32, 33, 68, 7, 13, 80, 92, 102, 99]
    }
}

class TestMosaic(unittest.TestCase):
    def test_pack(self):
        for b in list_test_bins():
            if b.lid not in PACKED:
                continue
            m = Mosaic(b)
            packed = m.pack()
            for col in ['y', 'x', 'roi_number']:
                values = packed[col].values
                expected_values = np.array(PACKED[b.lid][col])
                assert np.allclose(values, expected_values)