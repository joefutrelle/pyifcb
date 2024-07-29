import unittest

import numpy as np

from ifcb.tests.data.fileset_info import list_test_bins, get_fileset_bin
from ifcb.data.hdr import TEMPERATURE, HUMIDITY

from .test_ml_analyzed import TARGET_ML_ANALYZED

TARGET_METRICS = {
    'IFCB5_2012_028_081515': {
        'ml_analyzed': 0.0033914708,
        'run_time': 1.251953,
        'look_time': 0.813953,
        'inhibit_time': 0.438,
        'trigger_rate': 4.792512178971575,
        TEMPERATURE: 11.4799732421875,
        HUMIDITY:  32.167437512207,
    },
    'D20130526T095207_IFCB013': {
        'ml_analyzed': 4.8850699041666665,
        'run_time': 1184.037103,
        'look_time': 1172.416777,
        'inhibit_time': 11.620325999999977,
        'trigger_rate': 0.09965903914752577,
        TEMPERATURE: 35.270397,
        HUMIDITY: 2.48685,
    }
}

class TestBinMetrics(unittest.TestCase):
    @unittest.skip('pending validation of new ml_analyzed algorithm')
    def test_ml_analyzed(self):
        for met in list_test_bins():
            target = TARGET_METRICS[met.lid]
            assert np.isclose(met.ml_analyzed, target['ml_analyzed'])
            assert np.isclose(met.run_time, target['run_time'])
            assert np.isclose(met.look_time, target['look_time'])
            assert np.isclose(met.inhibit_time, target['inhibit_time'])            
    def test_trigger_rate(self):
        for met in list_test_bins():
            target = TARGET_METRICS[met.lid]
            assert np.isclose(met.trigger_rate, target['trigger_rate'])
    def test_header_metrics(self):
        for met in list_test_bins():
            target = TARGET_METRICS[met.lid]
            assert np.isclose(met.temperature, target[TEMPERATURE])
            assert np.isclose(met.humidity, target[HUMIDITY])
