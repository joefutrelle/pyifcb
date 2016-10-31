"""
Utilities for loading and saving IFCB data.
"""
import os

def load(*files):
    """
    Load raw IFCB data.

    Takes one or more raw data filenames (only one is required)
    which should all be in the same directory and differ
    only by extension.

    Typically, just pass the pathname of the ADC file.
    """
    from .files import Fileset, FilesetBin
    fs = Fileset(os.path.common_prefix(files))
    return FilesetBin(fs)

def load_hdf(hdf_path, group=None):
    """
    Load IFCB data from an HDF file.
    """
    from .hdf import HdfBin
    return HdfBin(hdf_path, group=group)

def load_zip(zip_path):
    from .zip import ZipBin
    return ZipBin(zip_path)

def load_mat(mat_path):
    from .matlab import MatBin
    return MatBin(mat_path)
