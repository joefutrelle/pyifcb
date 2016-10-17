
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

Bin is dict like. Keys are target numbers, values are ADC records.
ADC records are tuples. Bin provides a schema attribute indiciating
which schema is in use.

Attribute "images" is dict like, keys are target numbers, values are
raw images (no stitching, even for v1 IFCBs).

"headers" are immutable k/v pairs, with type conversion based on
guessing. Bin has PID which is a Pid object.

Can be backed by HDF, web services, zip. Can be instantiated
as HDF, zip.

"""

class BaseBin(object):
    """
    Abstract base class for Bin implementations.
    """
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
    @property
    def adc(self):
        """
        :returns pandas.DataFrame: ADC data as Pandas DataFrame
        """
        raise NotImplementedError
    # context manager default implementation
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
