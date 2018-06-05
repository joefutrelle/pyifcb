import unittest

from ifcb.data.zip import bin2zip, ZipBin
from ifcb.data.files import FilesetBin

from ifcb.tests.utils import withfile

from .fileset_info import list_test_bins
from .bins import assert_bin_equals

class TestZipBin(unittest.TestCase):
    @withfile
    def test_roundtrip(self, path):
        for out_bin in list_test_bins():
            with out_bin:
                bin2zip(out_bin, path)
                with ZipBin(path) as in_bin:
                    assert_bin_equals(in_bin, out_bin)
