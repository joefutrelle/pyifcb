import os
from UserDict import IterableUserDict

from functools32 import lru_cache

from .identifiers import Pid
from .adc import AdcFile
from .hdr import parse_hdr_file
from .roi import RoiFile
from .h5utils import hdfopen
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

def list_data_dirs(dirpath, blacklist=['skip'], sort=True):
    """return the path of any descendant directory that contains an .adc file
    parameters:
    blacklist - list of names to ignore
    sort - whether to sort output (does not guarantee that output
    is sorted by time"""
    dirlist = os.listdir(dirpath)
    if sort:
        dirlist.sort()
    for name in dirlist:
        if name[-3:] == 'adc':
            yield dirpath
            return
        elif name not in blacklist:
            child = os.path.join(dirpath,name)
            if os.path.isdir(child):
                # yield from recursive
                for dp in list_data_dirs(child):
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
    @property
    def adc_path(self):
        return self.basepath + '.adc'
    @property
    def hdr_path(self):
        return self.basepath + '.hdr'
    @property
    def roi_path(self):
        return self.basepath + '.roi'
    @property
    @lru_cache()
    def adc(self):
        return AdcFile(self.adc_path)
    @property
    @lru_cache()
    def roi(self):
        return RoiFile(self.adc, self.roi_path)
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
    @property
    def schema(self):
        return self.adc.schema
    @property
    def timestamp(self):
        return self.pid.timestamp
    def to_hdf(self, hdf_file, group=None, replace=True, archive=False):
        from .hdf import fileset2hdf
        fileset2hdf(self, hdf_file, group, replace, archive=archive)
    def __repr__(self):
        return '<IFCB Fileset %s>' % self.basepath
    def __str__(self):
        return self.basepath

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
    def __repr__(self):
        return '<DataDirectory %s>' % self.path
    def __str__(self):
        return self.path

# bin interface to Fileset

class FilesetBin(IterableUserDict, BaseBin):
    def __init__(self, fileset):
        IterableUserDict.__init__(self, fileset.adc)
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
    def to_hdf(self, path, group=None):
        self.fs.to_hdf(path, group)
