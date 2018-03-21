import unittest

import numpy as np

from ifcb.data.tests.fileset_info import list_test_bins, get_fileset_bin
from ifcb.data.hdr import TEMPERATURE, HUMIDITY

from .test_ml_analyzed import TARGET_ML_ANALYZED

from ..bin_metrics import BinMetrics

TARGET_METRICS = {
    'IFCB5_2012_028_081515': {
        'ml_analyzed': 0.003391470833333334,
        'run_time': 1.251953,
        'look_time': 0.8139530000000001,
        'trigger_rate': 5.59126420880017,
        TEMPERATURE: 11.4799732421875,
        HUMIDITY:  32.167437512207,
    },
    'D20130526T095207_IFCB013': {
        'ml_analyzed': 5.080841170833334,
        'run_time': 1231.024861,
        'look_time': 1219.401881,
        'trigger_rate': 0.09585509093954846,
        TEMPERATURE: 35.270397,
        HUMIDITY: 2.48685,
    }
}

class TestBinMetrics(unittest.TestCase):
    def test_toplevel_import(self):
        from ifcb.metrics import BinMetrics
    def test_ml_analyzed(self):
        for b in list_test_bins():
            target = TARGET_METRICS[b.lid]
            met = BinMetrics(b)
            assert np.isclose(met.ml_analyzed(), target['ml_analyzed'])
            assert np.isclose(met.run_time(), target['run_time'])
            assert np.isclose(met.look_time(), target['look_time'])
    def test_trigger_rate(self):
        for b in list_test_bins():
            target = TARGET_METRICS[b.lid]
            met = BinMetrics(b)
            assert np.isclose(met.trigger_rate(), target['trigger_rate'])
    def test_header_metrics(self):
        for b in list_test_bins():
            target = TARGET_METRICS[b.lid]
            met = BinMetrics(b)
            assert np.isclose(met.temperature(), target[TEMPERATURE])
            assert np.isclose(met.humidity(), target[HUMIDITY])
