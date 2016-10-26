import unittest

from ..utils import BaseDictlike

class MinimalBD(BaseDictlike):
    def __init__(self, a_dict):
        self.dict = a_dict
    def iterkeys(self):
        return self.dict.iterkeys()
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
            bd.iterkeys()
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
    def test_eq(self):
        d1 = dict(a=1,b=2,c=3)
        d2 = dict(a=1,b=2,c=3)
        d3 = dict(a=3,b=2,c=1)
        assert MinimalBD(d1) == MinimalBD(d2), '__eq__ failed'
        assert MinimalBD(d2) == MinimalBD(d1), '__eq__ failed'
        assert MinimalBD(d1) != MinimalBD(d3), '__ne__ failed'
        assert MinimalBD(d1) == d2, '__eq__ failed'
        assert MinimalBD(d1) != d3, '__ne__ failed'
