import unittest

from ..files import DataDirectory
from .fileset_info import list_test_bins, TEST_FILES

class TestHdr(unittest.TestCase):
	def test_hdr(self):
		for b in list_test_bins():
			h = b.headers
			eh = TEST_FILES[b.lid]['headers']
			for k,v in eh.items():
				assert h[k] == eh[k]