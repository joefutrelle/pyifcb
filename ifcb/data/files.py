import os

from functools32 import lru_cache

from .identifiers import Pid
from .adc import AdcFile
from .hdr import parse_hdr_file
from .roi import RoiFile
from .h5utils import hdfopen
from .utils import BaseDictlike
from .bins import BaseBin

"""
A well-formed raw data file path relative to some root
only contains path components that are
not blacklisted and either
either whitelisted or part of the file's LID.
"""

def validate_path(filepath, blacklist=['skip'], whitelist=['data']):
    assert set(blacklist).isdisjoint(set(whitelist))
    dirname, basename = os.path.split(filepath)
    lid, ext = os.path.splitext(basename)
    components = dirname.split(os.sep)
    for c in components:
        if c in blacklist:
            return False
        if c not in whitelist and c not in lid:
            return False
    return True

def list_filesets(dirpath, blacklist=['skip'], whitelist=['data'], sort=True, validate=True):
    """iterate over entire directory tree and return a Fileset
    object for each .adc/.hdr/.roi fileset found. warning: for
    large directories, this is slow.
    parameters:
    blacklist - list of names to ignore
    sort - whether to sort output (does not guarantee that output
    is sorted by time
    validate - whether to check the entire path for well-formedness
    (see above)"""
    assert set(blacklist).isdisjoint(set(whitelist))
    for dp, dirnames, filenames in os.walk(dirpath):
        for d in dirnames:
            if d in blacklist:
                dirnames.remove(d)
        if sort:
            dirnames.sort()
            filenames.sort()
        for f in filenames:
            basename, extension = f[:-4], f[-3:]
            if extension == 'adc' and basename+'.hdr' in filenames and basename+'.roi' in filenames:
                if validate:
                    reldir = dp[len(dirpath)+1:]
                    if not validate_path(os.path.join(reldir,basename), whitelist=whitelist, blacklist=blacklist):
                        continue
                yield dp, basename

def list_data_dirs(dirpath, blacklist=['skip'], sort=True, prune=True):
    """return the path of any descendant directory that contains an .adc file;
    parameters:
    blacklist - list of names to ignore
    sort - whether to sort output (does not guarantee that output
    is sorted by time).
    prune - whether, given a dir with an .adc file in it, to skip
    subdirectories
    """
    dirlist = os.listdir(dirpath)
    if sort:
        dirlist.sort()
    for name in dirlist:
        if name[-3:] == 'adc':
            yield dirpath
            if prune:
                return
    for name in dirlist:
        if name not in blacklist:
            child = os.path.join(dirpath,name)
            if os.path.isdir(child):
                # yield from recursive
                for dp in list_data_dirs(child, sort=sort, prune=prune):
                    yield dp

def find_fileset(dirpath, lid, whitelist=['data'], blacklist=['skip']):
    """find a fileset anywhere below the given directory path
    given the lid. This assumes that the file is contained in
    directories whose names are parts of the lid. directories
    with names on the whitelist are followed anyway. if the fileset
    is not found, returns None"""
    dirlist = os.listdir(dirpath)
    for name in dirlist:
        if name == lid + '.adc':
            basepath = os.path.join(dirpath,lid)
            return Fileset(basepath)
        elif name in whitelist or name in lid:
            # is the name whitelisted or contains part of the lid?
            fs = find_fileset(os.path.join(dirpath,name), lid, whitelist=whitelist, blacklist=blacklist)
            if fs is not None:
                return fs
    # not found
    return None
                                
class Fileset(object):
    def __init__(self, basepath):
        self.basepath = basepath
        self._roi = None
    @property
    def adc_path(self):
        return self.basepath + '.adc'
    @property
    def hdr_path(self):
        return self.basepath + '.hdr'
    @property
    def roi_path(self):
        return self.basepath + '.roi'
    # oo interface to files
    @property
    @lru_cache()
    def adc(self):
        return AdcFile(self.adc_path)
    @property
    def roi(self):
        # explicit cache management
        if self._roi is None:
            self._roi = RoiFile(self.adc, self.roi_path)
        return self._roi
    @property
    @lru_cache()
    def hdr(self):
        return parse_hdr_file(self.hdr_path)
    @property
    @lru_cache()
    def pid(self):
        return Pid(os.path.basename(self.basepath))
    @property
    def lid(self):
        return self.pid.bin_lid
    def exists(self):
        """checks for existence of all three raw data files"""
        if not os.path.exists(self.adc_path):
            return False
        if not os.path.exists(self.hdr_path):
            return False
        if not os.path.exists(self.roi_path):
            return False
        return True
    # metrics
    def getsizes(self):
        hdr_size = os.path.getsize(self.hdr_path)
        adc_size = os.path.getsize(self.adc_path)
        roi_size = os.path.getsize(self.roi_path)
        return {
            'hdr': hdr_size,
            'adc': adc_size,
            'roi': roi_size
        }
    def getsize(self):
        return sum(self.getsizes().values())
    @property
    def schema(self):
        return self.adc.schema
    @property
    def timestamp(self):
        return self.pid.timestamp
    def to_hdf(self, hdf_file, group=None, replace=True, archive=False):
        from .hdf import fileset2hdf
        fileset2hdf(self, hdf_file, group=group, replace=replace, archive=archive)
    def __repr__(self):
        return '<IFCB Fileset %s>' % self.basepath
    def __str__(self):
        return self.basepath
    # context management
    @property
    def isopen(self):
        return self._roi is not None
    def close(self):
        if not self.isopen:
            self._roi.close()
    def __exit__(self, *args):
        self.close()

class DataDirectory(object):
    def __init__(self, path='.', whitelist=['data'], blacklist=['skip']):
        self.path = path
        self.whitelist = whitelist
        self.blacklist = blacklist
    def list_filesets(self):
        for dirpath, basename in list_filesets(self.path, whitelist=self.whitelist, blacklist=self.blacklist):
            basepath = os.path.join(dirpath, basename)
            yield Fileset(basepath)
    def find_fileset(self, lid):
        return find_fileset(self.path, lid, whitelist=self.whitelist, blacklist=self.blacklist)
    def bin_iter(self):
        return (FilesetBin(fs) for fs in self)
    def list_bins(self):
        return list(self.bin_iter())
    def __iter__(self):
        # yield from list_filesets called with no keyword args
        for fs in self.list_filesets():
            yield fs
    def __contains__(self, lid):
        # fast contains method that avoids iteration
        return self.find_fileset(lid) is not None
    def __getitem__(self, lid):
        fs = self.find_fileset(lid)
        if fs is None:
            raise KeyError('No fileset for %s found at or under %s' % (lid, self.path))
        return fs
    def __len__(self):
        """warning: for large datasets, this is very slow"""
        return sum(1 for _ in self)
    # subdirectories
    def list_descendants(self, **kw):
        """find all 'leaf' data directories and yield DataDirectory
        objects for each one. Note that this enforces blacklisting
        but not whitelisting (no fileset path validation is done).'
        accepts list_data_dirs keywords, except 'blacklist' which
        takes on the value given in the constructor
        see list_data_dirs"""
        for dd in list_data_dirs(self.path, blacklist=self.blacklist, **kw):
            yield DataDirectory(dd)
    def __repr__(self):
        return '<DataDirectory %s>' % self.path
    def __str__(self):
        return self.path

# bin interface to Fileset

class FilesetBin(BaseDictlike, BaseBin):
    def __init__(self, fileset):
        self.fs = fileset
    @property
    def pid(self):
        return self.fs.pid
    @property
    def schema(self):
        return self.fs.schema
    @property
    def images(self):
        return self.fs.roi
    @property
    def headers(self):
        return self.fs.hdr
    @property
    def adc(self):
        return self.fs.adc.csv
    def to_hdf(self, path, **kw):
        self.fs.to_hdf(path, **kw)
    # dict implementation
    def iterkeys(self):
        for k in self.fs.adc:
            yield k
    def __getitem__(self, ix):
        return self.fs.adc[ix]
    def keys(self):
        return list(self)
    def has_key(self, k):
        return k in self.fs.adc
    def __contains__(self, k):
        return self.has_key(k)
    def __len__(self):
        return len(self.fs.adc)
    # context manager implementation
    def close(self):
        self.fs.close()
    def __exit__(self, *args):
        self.close()
    def __repr__(self):
        return '<FilesetBin %s>' % self
    def __str__(self):
        return self.fs.__str__()
