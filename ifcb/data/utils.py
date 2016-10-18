"""
Utilities for the IFCB data API.
"""

class BaseDictlike(object):
    """
    Provides as complete a readonly dict interface as possible,
    based on anything that implements ``iterkeys`` and ``__getitem__``.
    when overriding, override ``has_key`` rather than ```__contains__``.

    Override any method if a more efficient implementation
    is available.
    """
    def iterkeys(self):
        """
        Default implementation raises ``NotImplementedError``.
        This must be overridden for correct behavior.
        """
        raise NotImplementedError
    def __getitem__(self, k):
        """
        Default implementation raises ``NotImplementedError``.
        This must be overridden for correct behavior.
        """
        raise NotImplementedError
    def __iter__(self):
        return self.iterkeys()
    def keys(self):
        """
        Equivalent to ``list(self)``.

        :returns list: list of keys
        """
        return list(self)
    def has_key(self, k):
        """
        Iterates over keys and returns first key for
        which equality test passes. This method is
        called by the ``__contains__`` special method.

        :param k: the key to test.
        """
        for ek in self.iterkeys():
            if ek == k:
                return True
        return False
    def __contains__(self, k):
        return self.has_key(k)
    def iteritems(self):
        """
        Yields item pairs, based on calling iterkeys
        and then accessing each item.
        """
        for k in self.iterkeys():
            yield k, self[k]
    def items(self):
        """
        Equivalent to ``list(self.iteritems())``.

        :returns: list of key/value pairs
        """
        return list(self.iteritems())
    def itervalues(self):
        """
        Yields all values. Calls ``iteritems``.
        """
        for k, v in self.iteritems():
            yield v
    def values(self):
        """
        Collects the output of ``itervalues``.

        :returns list: list of values.
        """
        return list(self.itervalues())
    def __len__(self):
        n = 0
        for k in self.iterkeys():
            n += 1
        return n
    
