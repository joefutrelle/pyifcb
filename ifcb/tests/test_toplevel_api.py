import unittest

import ifcb

from .. import data

class TestToplevelAPI(unittest.TestCase):
    def test_existence(self):
        ifcb.SCHEMA_VERSION_1
        ifcb.SCHEMA_VERSION_2
        ifcb.DataDirectory
        ifcb.Pid
        ifcb.open_raw
        ifcb.open_hdf
        ifcb.open_zip
        ifcb.open_mat
        ifcb.open_url
        ifcb.parse_adc_file
        ifcb.parse_hdr_file
        ifcb.read_image
    def test_schemas(self):
        assert ifcb.SCHEMA_VERSION_1 is data.adc.SCHEMA_VERSION_1
        assert ifcb.SCHEMA_VERSION_2 is data.adc.SCHEMA_VERSION_2
