import unittest

from ifcb.data.io import open_raw, open_hdf, open_zip, open_mat

from ifcb.tests.utils import withfile

from .fileset_info import list_test_bins
from .bins import assert_bin_equals

class TestFormatConversionAPI(unittest.TestCase):
    @withfile
    def test_hdf_roundtrip(self, path):
        for out_bin in list_test_bins():
            with out_bin:
                out_bin.to_hdf(path)
                with open_hdf(path) as in_bin:
                    assert_bin_equals(in_bin, out_bin)
    @withfile
    def test_zip_roundtrip(self, path):
        for out_bin in list_test_bins():
            with out_bin:
                out_bin.to_zip(path)
                with open_zip(path) as in_bin:
                    assert_bin_equals(in_bin, out_bin)
    @withfile
    def test_mat_roundtrip(self, path):
        for out_bin in list_test_bins():
            with out_bin:
                out_bin.to_mat(path)
                with open_mat(path) as in_bin:
                    assert_bin_equals(in_bin, out_bin)

class TestOpenIdioms(unittest.TestCase):
    def test_open_raw(self):
        for a in list_test_bins():
            adc_path = a.fileset.adc_path
            b = open_raw(adc_path)
            assert_bin_equals(a, b)
    def test_open_cmgr(self):
        for a in list_test_bins():
            adc_path = a.fileset.adc_path
            with open_raw(adc_path) as b:
                assert_bin_equals(a, b)
