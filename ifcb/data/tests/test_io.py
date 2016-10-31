import unittest

from ..io import load, load_hdf, load_zip, load_mat

from ...tests.utils import withfile

from .fileset_info import list_test_bins
from .bins import assert_bin_equals

class TestFormatConversionAPI(unittest.TestCase):
    @withfile
    def test_hdf_roundtrip(self, path):
        for out_bin in list_test_bins():
            with out_bin:
                out_bin.to_hdf(path)
                with load_hdf(path) as in_bin:
                    assert_bin_equals(in_bin, out_bin)
    @withfile
    def test_zip_roundtrip(self, path):
        for out_bin in list_test_bins():
            with out_bin:
                out_bin.to_zip(path)
                with load_zip(path) as in_bin:
                    assert_bin_equals(in_bin, out_bin)
    @withfile
    def test_mat_roundtrip(self, path):
        for out_bin in list_test_bins():
            with out_bin:
                out_bin.to_mat(path)
                with load_mat(path) as in_bin:
                    assert_bin_equals(in_bin, out_bin)

