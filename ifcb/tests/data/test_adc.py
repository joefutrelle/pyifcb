import unittest
import shutil
import os

from ifcb.tests.utils import test_dir
from .fileset_info import list_test_filesets, TEST_FILES

from ifcb.data.adc import AdcFile

def list_adcs():
    for fs in list_test_filesets():
        yield AdcFile(fs.adc_path)
        
class TestAdcFile(unittest.TestCase):
    def test_size(self):
        for adc in list_adcs():
            assert adc.getsize() == os.path.getsize(adc.path)
    def test_parse(self):
        for adc in list_adcs():
            adc.to_dataframe()
    def test_one_based_index(self):
        for adc in list_adcs():
            df = adc.to_dataframe()
            assert df.index[0] == 1
    def test_csv_property(self):
        for adc in list_adcs():
            assert adc.to_dataframe() is adc.csv
    def test_len(self):
        for adc in list_adcs():
            assert len(adc) == len(adc.csv)
    def test_lid(self):
        for adc in list_adcs():
            assert adc.lid == adc.pid.lid
    def test_get_target(self):
        for adc in list_adcs():
            lid = adc.lid
            tf = TEST_FILES[lid]
            roi_number = tf['roi_number']
            h, w = tf['roi_shape']
            target = adc[roi_number]
            s = adc.schema
            assert target[s.ROI_WIDTH] == w
            assert target[s.ROI_HEIGHT] == h
