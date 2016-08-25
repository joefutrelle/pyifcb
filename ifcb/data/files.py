import os

from oii.utils import imemoize

from .identifiers import Pid

def list_filesets(dirpath, blacklist=['skip'], sort=True):
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
    """return the path of any directory that contains an .adc file"""
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
