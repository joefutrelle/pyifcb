"""
Utilities for IFCB data API
"""

class BaseDictlike(object):
    """Provides as complete a readonly dict interface as possible,
    based on anything that implements iterkeys and __getitem__.
    when overriding, override has_key rather than __contains__"""
    def iterkeys(self):
        raise NotImplementedError
    def __getitem__(self, k):
        raise NotImplementedError
    def __iter__(self):
        return self.iterkeys()
    def keys(self):
        return list(self)
    def has_key(self, k):
        for ek in self.iterkeys():
            if ek == k:
                return True
        return False
    def __contains__(self, k):
        return self.has_key(k)
    def iteritems(self):
        for k in self.iterkeys():
            yield k, self[k]
    def items(self):
        return list(self.iteritems())
    def itervalues(self):
        for k, v in self.iteritems():
            yield v
    def values(self):
        return list(self.itervalues())
    def __len__(self):
        n = 0
        for k in self.iterkeys():
            n += 1
        return n
    
