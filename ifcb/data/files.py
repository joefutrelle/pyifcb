import os

from functools32 import lru_cache

from .identifiers import Pid
from .adc import Adc
from .hdr import parse_hdr_file
from .roi import Roi

def list_filesets(dirpath, blacklist=['skip'], sort=True):
    """iterate over entire directory tree and return a Fileset
    object for each .adc/.hdr/.roi fileset found. warning: for
    large directories, this is slow.
    parameters:
    blacklist - list of names to ignore
    sort - whether to sort output (does not guarantee that output
    is sorted by time"""
    # FIXME implement faster version using scandir package
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
                yield dp, f[:-4]

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

def find_fileset(dirpath, lid):
    """find a fileset anywhere below the given directory path
    given the lid. This assumes that the file is contained in
    directories whose names are parts of the lid."""
    dirlist = os.listdir(dirpath)
    for name in dirlist:
        if name == lid + '.adc':
            return Fileset(os.path.join(dirpath,lid))
        else:
            try:
                lid.index(name)
                result = find_fileset(os.path.join(dirpath,name), lid)
                if result is not None:
                    return result
            except ValueError:
                pass
                                
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
        return Adc(self.adc_path)
    @property
    @lru_cache()
    def roi(self):
        return Roi(self.adc, self.roi_path)
    @property
    @lru_cache()
    def hdr(self):
        return parse_hdr_file(self.hdr_path)
    @property
    def pid(self):
        return Pid(os.path.basename(self.basepath))
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
    def timestamp(self):
        return self.pid.timestamp
    def __repr__(self):
        return '<Fileset %s>' % self.basepath
    def __str__(self):
        return self.basepath

class DataDirectory(object):
    def __init__(self, path):
        self.path = path
    def list_filesets(self, **kw):
        """use this instead of iteration interface if you want
        to pass keywords to list_filesets"""
        for dirpath, basename in list_filesets(self.path):
            basepath = os.path.join(dirpath, basename)
            yield Fileset(basepath)
    def find_fileset(self, lid):
        return find_fileset(self.path, lid)
    def __iter__(self):
        # yield from list_filesets called with no keyword args
        for fs in self.list_filesets():
            yield fs
    def __repr__(self):
        return '<DataDirectory %s>' % self.path
    def __str__(self):
        return self.path
