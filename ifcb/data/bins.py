"""
Bin API. Provides consistent access to IFCB raw data stored
in various formats.
"""

class Bin(object):
    """
    An abstract factory for ``Bin`` objects.
    """
    @staticmethod
    def from_fileset(fileset):
        """
        Create a ``Bin`` based on a ``Fileset``.

        :param fileset: the ``Fileset``
        :type fileset: Fileset
        :returns FilesetBin: the ``FilesetBin``
        """
        from .files import FilesetBin
        return FilesetBin(fileset)
    @staticmethod
    def from_files(*files):
        """
        Create a ``Bin`` from a list of three raw data files:
        the ``.adc``, ``.roi``, and ``.hdr`` files.

        :param files: the paths of the three files (in any order)
        :returns FilesetBin: the FilesetBin
        """
        from .files import Fileset
        fs = Fileset(os.path.common_prefix(files))
        return Bin.from_fileset(fs)
    @staticmethod
    def from_hdf(hdf_file, group=None):
        """
        Create a ``Bin`` from an HDF5 file.

        :param hdf_file: a pathname to an HDF file, or an open ``h5py.File`` or ``h5py.Group``
        :param group: an HDF path below the root containing the ``Bin``'s HDF data
        :returns HdfBin: the ``HdfBin``
        """
        from .hdf import HdfBin
        return HdfBin(hdf_file, group)
    
class BaseBin(object):
    """
    Abstract base class for Bin implementations.

    Bins are dict-like. Keys are target numbers, values are ADC records.
    ADC records are tuples.

    Context manager support is provided for implementations
    that must open files or other data streams.
    """
    @property
    def lid(self):
        """
        :returns str: the bin's LID.
        """
        return self.pid.bin_lid
    @property
    def timestamp(self):
        """
        :returns datetime: the bin's timestamp.
        """
        return self.pid.timestamp
    @property
    def schema(self):
        """
        The IFCB schema in use. Schemas provide indices into
        ADC records. For example, given a bin ``B`` with a
        target number 5, the following code retrieves the x
        position of the target ROI:

        :Example:

        >>> B[5][B.schema.ROI_X]
        234

        """
        from .adc import SCHEMA
        return SCHEMA[self.pid.schema_version]
    # context manager default implementation
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
