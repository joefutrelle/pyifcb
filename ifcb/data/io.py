"""
Utilities for opening and saving IFCB data.
"""
import os

def open_raw(*files):
    """
    Open raw IFCB data.

    Takes one or more raw data filenames (only one is required)
    which should all be in the same directory and differ
    only by extension.

    Typically, just pass the pathname of the ADC file.
    """
    from .files import Fileset, FilesetBin
    basepath = os.path.commonprefix(files)
    basepath, _ = os.path.splitext(basepath)
    fs = Fileset(basepath)
    return FilesetBin(fs)

def open_hdf(hdf_path, group=None):
    """
    Open IFCB data from an HDF file.
    """
    from .hdf import HdfBin
    return HdfBin(hdf_path, group=group)

def open_zip(zip_path):
    from .zip import ZipBin
    return ZipBin(zip_path)

def open_mat(mat_path):
    from .matlab import MatBin
    return MatBin(mat_path)
