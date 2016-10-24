"""
Support for reading and writing IFCB data to HDF5.
"""

import datetime

import numpy as np
from functools32 import lru_cache

from .h5utils import pd2hdf, hdf2pd, hdfopen, H5_REF_TYPE

from .identifiers import Pid
from .adc import SCHEMA
from .utils import BaseDictlike
from .bins import BaseBin

def adc2hdf(adcfile, hdf_file, group=None, replace=True):
    """
    Store an ``AdcFile`` in an HDF file or group. ADC
    data is represented as a ``pandas.DataFrame`` with
    a ``schema`` attribute specifying the name of the
    ADC schema.

    :param adcfile: the ``AdcFile`` to store
    :type adcfile: AdcFile
    :param hdf_file: the root HDF
      object (h5py.File or h5py.Group) in which to write
      the ADC data
    :param group: a path below the sub-group
      to use
    :param replace: whether to replace any existing data
      at that location in the HDF file
    """
    with hdfopen(hdf_file, group, replace=replace) as root:
        pd2hdf(root, adcfile.to_dataframe(), compression='gzip')
        root.attrs['schema'] = adcfile.schema.name

def roi2hdf(roifile, hdf_file, group=None, replace=True):
    """
    Store a ``RoiFile`` in an HDF file or group. ROI
    data is represented as follows in an HDF group:

    * ``{root}.index`` (attribute): target number for each image
    * ``{root}/images`` (dataset): references to images keyed by target number
    * ``{root}/{n}`` (dataset): 2d uint8 image (n = ``str(target_number)``)

    :param roifile: the ``RoiFile`` to store
    :type roifile: RoiFile
    :param hdf_file: the root HDF
      object (h5py.File or h5py.Group) in which to write
      the image data and index
    :param group: a path below the sub-group
      to use
    :param replace: whether to replace any existing data
      at that location in the HDF file
    """
    with hdfopen(hdf_file, group, replace=replace) as root:
        root.attrs['index'] = roifile.index
        # create image datasets and map them to roi numbers
        d = { n: root.create_dataset(str(n), data=im) for n, im in roifile.iteritems() }
        # now create sparse array of references keyed by roi number
        n = max(d.keys())+1
        r = [ d[i].ref if i in d else None for i in range(n) ]
        root.create_dataset('images', data=r, dtype=H5_REF_TYPE)

def hdr2hdf(hdr_dict, hdf_file, group=None, replace=True):
    """
    Store a header dict in an HDF file or group. Header data
    is represented in HDF as a set of attributes on the group.

    :param hdr_dict: the headers
    :type hdr_dict: dict
    :param hdf_file: the root HDF
      object (h5py.File or h5py.Group) on which to write
      the header attributes
    :param group: a path below the sub-group
      to use
    :param replace: whether to replace any existing data
      at that location in the HDF file
    """
    with hdfopen(hdf_file, group, replace=replace) as root:
        for k, v in hdr_dict.items():
            root.attrs[k] = v

def file2hdf(hdf_root, ds_name, path, **kw):
    """
    Write the contents of a file to an HDF dataset. Keywords are
    passed through to ``h5py.create_dataset``.

    :param hdf_root: an open ``h5py.File`` or ``h5py.Group`` in which
      to create the dataset
    :param ds_name: the name to give the dataset
    :param path: the file path
    """
    with open(path,'rb') as infile:
        file_data = infile.read()
    file_array = bytearray(file_data)
    hdf_root.create_dataset(ds_name, data=file_array, **kw)

def hdf2file(hdf_dataset, path):
    """
    Write the contents of an HDF dataset to a file. Does not stream,
    so the entire contents of the dataset must fit in memory.

    :param hdf_dataset: an ``h5py.Dataset`` to read
    :param path: the path of the file to write
    """
    file_data = bytearray(hdf_dataset)
    with open(path,'wb') as outfile:
        outfile.write(file_data)

def fileset2hdf(fileset, hdf_file, group=None, replace=True, archive=False):
    """
    Write a ``Fileset`` to an HDF file.

    A ``Fileset`` is represented in HDF relative to some root path as:

    * ``{root}.pid`` (attribute) - full base pathname
    * ``{root}.lid`` (attribute) - bin LID
    * ``{root}.timestamp`` (attribute) - bin timestamp in ISO8601 UTC format
    * ``{root}/hdr`` (group) - see hdr2hdf
    * ``{root}/adc`` (group) - see adc2hdf
    * ``{root}/roi`` (group) - see roi2hdf
    * ``{root}/archive`` (group) - optional: archived files
    * ``{root}/archive/adc`` (dataset) - archived ``.adc`` file
    * ``{root}/archive/hdr`` (dataset) - archived ``.hdr`` file

    :param fileset: the ``Fileset`` to write
    :type fileset: Fileset
    :param hdf_file: the root HDF file pathname or
      object (h5py.File or h5py.Group) on which to write
      the IFCB data
    :param group: a path below the sub-group
      to use
    :param replace: whether to replace any existing data
      at that location in the HDF file
    :param archive: whether to store copies of the ``.adc`` and ``.hdr``
      files in the HDF file
    """
    with hdfopen(hdf_file, group, replace=replace) as root:
        root.attrs['pid'] = str(fileset.pid)
        root.attrs['lid'] = fileset.lid
        root.attrs['timestamp'] = fileset.timestamp.isoformat()
        hdr2hdf(fileset.hdr, root, 'hdr', replace=replace)
        adc2hdf(fileset.adc, root, 'adc', replace=replace)
        roi2hdf(fileset.roi, root, 'roi', replace=replace)
        if archive:
            file2hdf(root, 'archive/adc', fileset.adc_path, compression='gzip')
            file2hdf(root, 'archive/hdr', fileset.hdr_path)

def hdf2fileset(hdf_path, fileset_path, group=None):
    """
    Unarchive an archived IFCB fileset from an HDF file. Creates
    ``.hdr``, ``.adc``, and ``.roi`` files exactly matching the
    original raw data. This is the inverse operation of
    ``fileset2hdf`` if it was called with ``archive`` set to True.

    :param hdf_path: the path to the HDF file
    :param fileset_path: base path for output files
    :param group: (optional) the path to the HDF group containing
      the archived IFCB data
    """
    with hdfopen(hdf_path, group) as root:
        if not 'archive' in root:
            raise ValueError('no archived IFCB data found')
        hdf2file(root['archive/adc'], fileset_path + '.adc')
        hdf2file(root['archive/hdr'], fileset_path + '.hdr')
        with open(fileset_path + '.roi', 'wb') as outroi:
            schema1 = root['adc'].attrs['schema'] == SCHEMA[1].name
            if schema1:
                outroi.write("\0")
            imref = root['roi/images']
            for i in root['roi'].attrs['index']:
                image = root[imref[i]]
                outroi.write(np.array(image).ravel())
            if schema1:
                outroi.write("\0")
        
# bin interface to HDF

class HdfRoi(BaseDictlike):
    """
    Dict-like interface to IFCB images stored in an HDF file.
    """
    def __init__(self, group):
        """
        :param group: the ``h5py.Group`` containing the image data
        """
        self._group = group
    def iterkeys(self):
        for k in self._group.attrs['index']:
            yield k
    def __len__(self):
        return len(self._group.attrs['index'])
    def __getitem__(self, roi_number):
        return np.array(self._group[self._group['images'][roi_number]])
        
class HdfBin(BaseBin, BaseDictlike):
    """
    Bin interface to HDF file/group.

    Context manager implementation opens and closes the HDF file.
    This implementation is caching, so if the HDF file changes during
    an instance's lifecycle, those changes may not be reflected in
    subsequent accesses.
    """
    def __init__(self, hdf_file, group=None):
        """
        :param hdf_file: HDF file path or open ``h5py.Group`` containing bin data
        :param group: (optional) path in HDF file/group containing bin data
        """
        # open the file or group
        self._open_params = (hdf_file, group)
        self._hdf = None
        self._open()
    # context manager implementation
    @property
    def isopen(self):
        """
        :returns bool: if HDF file is open
        """
        return self._hdf is not None
    def _open(self):
        assert not self.isopen, 'HdfBin already open'
        self._hdf = hdfopen(*self._open_params)
        self._group = self._hdf.group
    def close(self):
        """
        Close the HDF file. Will fail if HDF file is already
        closed.
        """
        assert self.isopen, 'HdfBin is already closed'
        self._hdf.close()
        self._hdf = None
    def __enter__(self):
        return self
    def __exit__(self, *args):
        if self.isopen:
            self.close()
    # Dictlike
    @property
    @lru_cache()
    def adc(self):
        """
        adc(self)
        The bin's ADC data as a ``pandas.DataFrame``
        """
        return hdf2pd(self._group['adc'])
    @property
    @lru_cache()
    def schema(self):
        """
        The bin's schema
        """
        return SCHEMA[self._group['adc'].attrs['schema']]
    @lru_cache()
    def get_target(self, target_number):
        """
        Retrieve a target record by target number

        :param target_number: the target number
        """
        d = tuple(self.adc[c][target_number] for c in self.adc.columns)
        return d
    def __getitem__(self, target_number):
        return self.get_target(target_number)
    def has_key(self, k):
        return k in self.adc.index
    def iterkeys(self):
        for k in self.adc.index:
            yield k
    def __len__(self):
        return len(self.adc.index)
    @property
    @lru_cache()
    def headers(self):
        """
        The bin's headers
        """
        return dict(self._group['hdr'].attrs)
    @property
    @lru_cache()
    def pid(self):
        """
        The bin's ``Pid``
        """
        return Pid(self._group.attrs['pid'])
    @property
    def images(self):
        """
        The bin's images
        """
        return HdfRoi(self._group['roi'])
