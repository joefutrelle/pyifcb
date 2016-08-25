import pandas as pd

from oii.ifcb2 import get_resolver
from oii.utils import imemoize

def parse(pid):
    # FIXME implement w/o resolver
    try:
        return get_resolver().ifcb.pid(pid=pid).next()
    except StopIteration:
        raise ValueError('invalid PID syntax: %s' % pid)

class Pid(object):
    """represents the permanent ID of a bin"""
    def __init__(self, pid, parse=True):
        self.pid = pid
        if parse:
            self.parsed
    def isvalid(self):
        try:
            self.parsed
            return True
        except ValueError:
            pass
        return False
    @property
    @imemoize
    def parsed(self):
        return parse(self.pid)
    @property
    def schema_version(self):
        return int(self.parsed['schema_version'][1:])
    @property
    def timestamp(self):
        return pd.to_datetime(self.parsed['timestamp'], format=self.parsed['timestamp_format'], utc=True)
    @property
    @imemoize
    def schema(self):
        """return ADC columns"""
        # FIXME move elsewhere
        return self.parsed['adc_cols'].split(' ')
    def __getattr__(self, name):
        if name in ['bin_lid', 'lid', 'instrument', 'namespace', 'product', 'target', 'ts_label']:
            return self.parsed[name]
        else:
            return self.__getattribute__(name)
    def __repr__(self):
        return '<pid %s>' % self.pid
    def __str__(self):
        return self.pid
