
class Bin(object):
    """
    An abstract factory for Bin objects.
    """
    @staticmethod
    def from_fileset(fileset):
        """
        Create a Bin based on a Fileset.

        :param fileset: the Fileset
        :type fileset: Fileset
        :returns FilesetBin: the FilesetBin
        """
        from ifcb.data.files import FilesetBin
        return FilesetBin(fileset)
    @staticmethod
    def from_files(*files):
        """
        Create a Bin from a list of three raw data files:
        the .adc, .roi, and .hdr files.

        :param files: the paths of the three files (in any order)
        :returns FilesetBin: the FilesetBin
        """
        from ifcb.data.files import Fileset
        fs = Fileset(os.path.common_prefix(files))
        return Bin.from_fileset(fs)
    @staticmethod
    def from_hdf(hdf_file, group=None):
        """
        Create a Bin from an HDF file.

        :param hdf_file: a pathname to an HDF file, or an open h5.File or h5.Group;
        :param group: an HDF path below the root containing the Bin's HDF data
        :returns HdfBin: the HdfBin
        """
        from ifcb.data.hdf import HdfBin
        return HdfBin(hdf_file, group)

"""Bin API

Bin is dict like. Keys are ROI numbers, values are ADC records
(modified for stitching for v1). ADC records are tuples. Bin
provides a schema attribute indiciating which schema is in use

Attribute "images" is dict like, keys are ROI numbers, values are
stitched images (with NaNs in unfilled areas) No access to unstitched
images (use RoiFile for that). "headers" are immutable k/v pairs, with
type conversion based on guessing? FIXME "context" heading from old
style IFCBs not represented properly in HDF. Bin has PID which is a
Pid object

Can be backed by HDF, web services, zip. Can be instantiated
as HDF, zip.

"""

class BaseDictlike(object):
    """provides as complete a readonly dict interface as possible,
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
    
class BaseBin(object):
    @property
    def pid(self):
        raise NotImplementedError
    @property
    def lid(self):
        return self.pid.bin_lid
    @property
    def timestamp(self):
        return self.pid.timestamp
    @property
    def schema(self):
        raise NotImplementedError
    @property
    def images(self):
        raise NotImplementedError
    @property
    def headers(self):
        raise NotImplementedError
    # context manager default implementation
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
