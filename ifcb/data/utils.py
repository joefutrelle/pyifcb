"""
Utilities for the IFCB data API.
"""

from collections.abc import Mapping

class CaseInsensitiveDict(Mapping):
    def __init__(self, d):
        self._d = d
        self._s = dict((k.lower(), k) for k in d)
    def __contains__(self, k):
        return k.lower() in self._s
    def __len__(self):
        return len(self._s)
    def __iter__(self):
        return iter(self._d)
    def __getitem__(self, k):
        return self._d[self._s[k.lower()]]
    def actual_key_case(self, k):
        return self._s.get(k.lower())

class BaseDictlike(object):
    """
    Provides as complete a readonly dict interface as possible,
    based on anything that implements ``keys`` and ``__getitem__``.
    when overriding, override ``has_key`` rather than ```__contains__``.

    Override any method if a more efficient implementation
    is available.
    """
    def keys(self):
        """
        Default implementation raises ``NotImplementedError``.
        This must be overridden for correct behavior.
        """
        raise NotImplementedError
    def __getitem__(self, k):
        """
        Default implementation raises ``NotImplementedError``.
        This must be overridden for correct behavior.

        :param k: the key
        :type k: hashable
        """
        raise NotImplementedError
    def __iter__(self):
        yield from self.keys()
    def has_key(self, k):
        """
        Iterates over keys and returns first key for
        which equality test passes. This method is
        called by the ``__contains__`` special method.

        :param k: the key to test
        :type k: hashable
        """
        for ek in self.keys():
            if ek == k:
                return True
        return False
    def __contains__(self, k):
        return self.has_key(k)
    def items(self):
        """
        Yields item pairs, based on calling keys
        and then accessing each item.
        """
        for k in self.keys():
            yield k, self[k]
    def values(self):
        """
        Yields all values. Calls ``items``.
        """
        for k, v in self.items():
            yield v
    def __len__(self):
        n = 0
        for k in self.keys():
            n += 1
        return n
    
