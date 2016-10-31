import unittest

from ..matlab import bin2mat, MatBin

from ...tests.utils import withfile

from .fileset_info import list_test_bins
from .bins import assert_bin_equals

class TestMatBin(unittest.TestCase):
    @withfile
    def test_roundtrip(self, path):
        for out_bin in list_test_bins():
            with out_bin:
                bin2mat(out_bin, path)
                with MatBin(path) as in_bin:
                    assert_bin_equals(in_bin, out_bin)
