"""
Support for parsing IFCB permanent identifiers (a.k.a., pids).
"""

import re

from functools32 import lru_cache
import pandas as pd

### parsing

# supports time-like regexes e.g., IFCB9_yyyy_YYY_HHMMSS
@lru_cache()
def timestamp2regex(pattern):
    """
    Convert a special "timestamp" expression into a regex pattern.
    The expression is treated as an ordinary regex except that special
    patterns are used to define groups that match typical patterns that
    are found in timestamps and timestamp-related formats.

    Special patterns that define groups that are supported:

    * ``0-9`` - where n is any number of digits (e.g., ``111``, ``88``) fixed-length
      decimal number
    * ``s`` - any number of ``s``'s indicating milliseconds (e.g., ``sss``)
    * ``yyyy`` - four-digit year
    * ``mm`` - two-digit (left-zero-padded) month
    * ``dd`` - two-digit (left-zero-padded) day of month
    * ``DDD`` - three-digit (left-zero-padded) day of year
    * ``HH`` - two-digit (left-zero-padded) hour of day
    * ``MM`` - two-digit (left-zero-padded) minute of hour
    * ``SS`` - two-digit (left-zero-padded) second of minute
    * ``#`` - any string of digits (non-capturing)
    * ``i`` - an "identifier" (e.g., ``jpg2000``) (non-capturing)
    * ``.ext`` - a file extension
    * ``.`` - a literal dot
    * ``\.`` - a regex dot (matches any character)
    * ``any`` - a regex ``.*``

    Example patterns:

    * ``yyyy-mm-ddTHH:MM:SSZ`` - a UTC ISO8601 timestamp
    * ``yyyyDDD`` - year and day of year

    :Example:

    >>> timestamp2regex('Dyyyymm')
    'D(?P<yyyy>[0-9]{4})(?P<mm>0[1-9]|1[0-2])'

    :param pattern: the pattern
    :type pattern: str
    """
    # FIXME handle unfortunate formats such as
    # - non-zero-padded numbers
    # - full and abbreviated month names
    # first, do fixed-length numbers (requires some trickery)
    start, result = 0, ''
    for m in re.finditer(r'(([0-9])\2*)',pattern):
        s = m.start()
        result = result + pattern[start:s]
        l, n = len(m.group(0)), m.group(1)
        result += '(?P<n%s>[0-9]{%d})' % (n, l)
        start = m.end()
    pattern = result + pattern[start:]
    pattern = re.sub(r's+','(?P<sss>[0-9]+)',pattern) # milliseconds
    pattern = re.sub(r'yyyy','(?P<yyyy>[0-9]{4})',pattern) # four-digit year
    pattern = re.sub(r'mm','(?P<mm>0[1-9]|1[0-2])',pattern) # two-digit month
    pattern = re.sub(r'dd','(?P<dd>0[1-9]|[1-2][0-9]|3[0-1])',pattern) # two-digit day of month
    pattern = re.sub(r'DDD','(?P<DDD>[0-3][0-9][0-9])',pattern) # three-digit day of year
    pattern = re.sub(r'HH','(?P<HH>[0-1][0-9]|2[0-3])',pattern) # two-digit hour
    pattern = re.sub(r'MM','(?P<MM>[0-5][0-9])',pattern) # two-digit minute
    pattern = re.sub(r'SS','(?P<SS>[0-5][0-9])',pattern) # two-digit second
    pattern = re.sub(r'#','[0-9]+',pattern) # any string of digits (non-capturing)
    pattern = re.sub(r'i','[a-zA-Z][a-zA-Z0-9_]*',pattern) # an identifier (e.g., jpg2000) (non-capturing)
    pattern = re.sub(r'\.ext',r'(?:.(?P<ext>[a-zA-Z][a-zA-Z0-9_]*))',pattern) # a file extension
    pattern = re.sub(r'\.',r'\.',pattern) # a literal '.'
    pattern = re.sub(r'\\.','.',pattern) # a regex '.'
    pattern = re.sub(r'any','.*',pattern) # a regex .*
    return pattern

# "timetsamp"-style patterns
V1_PID_PATTERN = '(IFCB1_(yyyy_DDD_HHMMSS))(any)'
V2_PID_PATTERN = '(D(yyyymmddTHHMMSS)_IFCB111)(any)'

@lru_cache()
def c(pattern):
    """
    Compile a regex pattern (with caching)

    :param pattern: the pattern
    :type pattern: str
    :returns: the compiled pattern
    """
    return re.compile(pattern)

@lru_cache()
def m(pattern, string):
    """
    Match a pattern against a string and return the
    matching groups. Provides several convenience
    features that differ from ``re.match``:

    * If the pattern does not match the string, or the
      string is None, return a tuple of Nones the length
      of the number of capturing groups.
    * If there is only one pattern, return a single
      value instead of a one-element tuple.

    :param pattern: the pattern
    :type pattern: str
    :param string: the string to match
    :returns: a value or tuple of captured groups
    """
    def col_or_scalar(o):
        if len(o) == 1:
            return o[0]
        else:
            return o
    def nones(n):
        return col_or_scalar([None for _ in range(n)])
    r = c(pattern)
    n = r.groups
    if string is None:
        return nones(n)
    m = r.match(string)
    if m is None:
        return nones(n)
    return col_or_scalar(tuple(m.groups()))

def parse(pid):
    """
    Parse an IFCB permanent identifier (a.k.a., "pid"). The
    passed-in pid may contain either a pathname prefix or
    a URL prefix, and may include a product identifier and/or
    extension. It can also include a target number.
    The pid syntax is specified elsewhere. Extracted fields
    are returned as a dict.

    :param pid: the pid as a string

    Example pids:

    * ``D20160714T023910_IFCB101``
    * ``IFCB3_2008_013423.adc``
    * ``http://mysite.org/data/D20150321T124431_IFCB103``
    * ``D20160714T023910_IFCB101_00014.png``
    * ``/my/directory/D20160603T002950_IFCB101_blob.zip``

    Fields extracted include:

    * ``pid`` - the pid, minus any leading path/URL prefix
    * ``lid`` - the pid, minus all prefixes and suffixes
    * ``namespace`` - any leading path/URL prefix
    * ``ts_label`` - for URL patterns, the time series label
    * ``year``, ``month``, ``day`` - the date
    * ``hour``, ``minute``, ``second`` - the time
    * ``instrument`` - the instrument number
    * ``timestamp`` - the complete timestamp
    * ``timestamp_format`` - the format specifier of the timestamp
    * ``schema_version`` - which revision of the instrument
      (1 for ``IFCB...`` pids, 2 for ``D...`` pids)
    * ``yearday`` - the year and day, concatenated
    * ``target`` - the target number (if any)
    * ``extension`` - the extension, not including the leading ``.``
    * ``product`` - the product type identifier, or 'raw' if
      not specified

    :param pid: the pid
    :type pid: str
    :returns dict: fields extraced from the pid
    """
    pid = c(r'^.*\\').sub('',pid) # strip Windows dirs
    namespace, suffix = m('(.*/)?(.*)',pid)
    ts_label = m('(?:.*/)?(.*)/$',namespace)
    # try v2 identifier pattern
    bin_lid, timestamp, year, month, day, hour, minute, second, instrument, tpe = m(timestamp2regex(V2_PID_PATTERN),suffix)
    # try v1 identifier pattern
    if bin_lid is None:
        bin_lid, instrument, timestamp, year, day, hour, minute, second, tpe = m(timestamp2regex(V1_PID_PATTERN),suffix)
        schema_version = 1
        timestamp_format = '%Y_%j_%H%M%S'
        if year is None or day is None:
            raise ValueError('invalid pid: %s' % pid)
        yearday = '_'.join([year, day])
    else:
        schema_version = 2
        timestamp_format = '%Y%m%dT%H%M%S'
        yearday = ''.join([year, month, day])
    if bin_lid is None: # syntax error
        raise ValueError('invalid pid: %s' % pid)
    # now parse target, product, and extension (tpe)
    # tpe, if not empty, must start with _ or .
    if tpe and (tpe[:1] not in '._' or len(tpe) < 2):
        raise ValueError('invalid target, product, or extension: %s' % pid)
    target, product, extension = m(r'(?:_([0-9]+))?(?:_([a-zA-Z][a-zA-Z0-9_]*))?(?:\.([a-zA-Z][a-zA-Z0-9]*))?',tpe)
    if product is None:
        product = 'raw'
    if target is not None:
        lid = '_'.join([bin_lid, target])
    else:
        lid = bin_lid # make sure both are present
    # now del non-desired locals
    del tpe
    # this might actually be an acceptable use of locals()
    return locals()

def unparse(parsed):
    """
    Unparse a PID. Accepts a parsed PID or anything containing
    the appropriate fields. Minimally, must include

    * ``schema_version``
    * ``instrument``
    * either ``year``, ``month``, ``day`` (day-of-month);
      or, ``year``, ``day`` (day-of-year)
    * ``hour``, ``minute``, ``second``

    May also include

    * ``namespace``
    * ``product``
    * ``extension``
    * ``target``

    """
    try:
        schema_version = int(parsed['schema_version'])
        instrument = int(parsed['instrument'])
        year = int(parsed['year'])
        day = int(parsed['day'])
        hour = int(parsed['hour'])
        minute = int(parsed['minute'])
        second = int(parsed['second'])

        product = parsed.get('product','raw')
        namespace = parsed.get('namespace')

        if namespace is None:
            namespace = ''
            
        if 'target' in parsed and parsed['target'] is not None:
            tstring = '_%05d' % int(parsed['target'])
        else:
            tstring = ''

        if product == 'raw' or product is None:
            pstring = ''
        else:
            pstring = '_%s' % product

        if 'extension' in parsed and parsed['extension'] is not None:
            estring = '.%s' % parsed['extension']
        else:
            estring = ''

        suffix = '%s%s%s' % (tstring, pstring, estring)

        if schema_version == 1:
            fmt = '%sIFCB%1d_%4d_%03d_%02d%02d%02d%s'
            vals = (namespace, instrument, year, day, hour, minute, second, suffix)

        elif schema_version == 2:
            month = int(parsed['month'])
            fmt = '%sD%4d%02d%02dT%02d%02d%02d_IFCB%03d%s'
            vals = (namespace, year, month, day, hour, minute, second, instrument, suffix)
            
        else:
            raise ValueError('unknown schema version %d' % schema_version)
        
        return fmt % vals

    except KeyError:
        raise ValueError('cannot unparse PID')
        
class Pid(object):
    """
    Represents the permanent identifier of an IFCB bin.
    Provides attribute-based access to the relevant parsed
    fields of a PID. ``Pid``s sort by alpha.
    """
    def __init__(self, pid, parse=True):
        """
        Construct a Pid object from a string.
        Parsing is optional in case it needs
        to be deferred.

        :param pid: the pid
        :param parse: whether to parse
        """
        self.pid = pid
        self._parsed = None
        if parse:
            self.parsed
    def isvalid(self):
        """
        Check this PID for validity.
        """
        try:
            self.parsed # parse if not already
            return True
        except ValueError:
            pass
        return False
    def copy(self):
        new_pid = Pid(self.pid, parse=False)
        if self._parsed is not None:
            # avoid re-parsing
            new_pid._parsed = self._parsed.copy()
        return new_pid
    def __cmp__(self, other):
        try:
            if self.pid < other.pid:
                return -1
            elif self.pid > other.pid:
                return 1
        except AttributeError:
            if self.pid < other:
                return -1
            elif self.pid > other:
                return 1
        else:
            return 0
    def __eq__(self, other):
        try:
            return self.pid == other.pid
        except AttributeError:
            return self.pid == other
    @property
    def parsed(self):
        """
        The parsed PID
        """
        if self._parsed is None:
            # convert some properties to int
            p = parse(self.pid)
            for ip in ['target', 'instrument', 'schema_version']:
                if p[ip] is not None:
                    p[ip] = int(p[ip])
            self._parsed = p
        return self._parsed
    def __getattr__(self, name):
        try:
            return self.parsed[name]
        except KeyError:
            raise AttributeError
    def with_target(self, target_number, namespace=True):
        """
        Add a target number to the pid's bin_lid. Does not
        include product or extension. Optionally includes
        namespace prefix. This is more efficient than the
        following approach, which will preserve product
        and extension:

        >>> my_pid = Pid('IFCB1_2000_001_123456_blob')
        >>> new_pid = my_pid.copy()
        >>> new_pid.target = 927
        >>> new_pid
        <pid IFCB1_2000_001_123456_00927_blob>

        :param target_number: the target number
        :type target_number: int
        :param namespace: whether to include the namespace prefix
        :type namespace: bool
        :returns: the target ID (as a string)
        """
        ns = ''
        if namespace and self.namespace is not None:
            ns = self.namespace
        return ns + self.bin_lid + '_%05d' % target_number
    @property
    def timestamp(self):
        """
        The timestamp of the bin as a ``datetime``
        """
        return pd.to_datetime(self.parsed['timestamp'], format=self.parsed['timestamp_format'], utc=True)
    def __setattr__(self, name, value):
        if name == 'target':
            self.parsed # ensure parsing is complete
            self._parsed.update({ name: int(value) })
            self.pid = unparse(self._parsed)
        elif name in ['product', 'extension']:
            self.parsed # ensure parsing is complete
            self._parsed.update({ name: value })
            self.pid = unparse(self._parsed)
        else:
            super(Pid, self).__setattr__(name, value)
    def __repr__(self):
        return '<pid %s>' % self.pid
    def __str__(self):
        return self.pid
