import unittest

from ifcb.data.utils import BaseDictlike

class MinimalBD(BaseDictlike):
    def __init__(self, a_dict):
        self.dict = a_dict
    def keys(self):
        return self.dict.keys()
    def __getitem__(self, k):
        return self.dict[k]
            
class TestBaseDictlike(unittest.TestCase):
    def setUp(self):
        self.keys = 'abc'
        self.values = '123'
        self.bad_keys = 'xyz'
        self.d = dict(zip(self.keys, self.values))
        self.bd = MinimalBD(self.d)
    def test_not_implemented(self):
        bd = BaseDictlike()
        with self.assertRaises(NotImplementedError):
            bd.keys()
        with self.assertRaises(NotImplementedError):
            bd[0]
    def test_iter(self):
        bd_keys = set(self.bd)
        assert set(self.keys) == bd_keys
    def test_keys(self):
        assert set(self.keys) == set(self.bd.keys())
    def test_values(self):
        assert set(self.values) == set(self.bd.values())
    def test_contains(self):
        for k in self.keys:
            assert self.bd.has_key(k), 'missing key'
            assert k in self.bd, 'has_key does not agree with __contains__'
        for k in self.bad_keys:
            assert not self.bd.has_key(k), 'spurious key'
            assert k not in self.bd, 'has_key does not agree with __contains__'
    def test_len(self):
        assert len(self.keys) == len(self.bd), 'inconsistent lengths'
