import datetime

import numpy as np
from functools32 import lru_cache

from .h5utils import df2h5, h52df, open_h5_group, H5_REF_TYPE, opengroup

from .identifiers import Pid
from .adc import SCHEMA
from .bins import BaseBin, BaseDictlike

def adc2hdf(adcfile, hdf_file, group=None, replace=True):
    """an ADC file is represented as a Pandas DataFrame
    with 'schema' attr naming schema version"""
    with open_h5_group(hdf_file, group, replace=replace) as g:
        df2h5(g, adcfile.to_dataframe(), compression='gzip')
        g.attrs['schema'] = adcfile.schema.name

def roi2hdf(roifile, hdf_file, group=None, replace=True):
    """ROI layout given {root}
    {root}.index (attribute): roi number for each image
    {root}/images (dataset): references to images keyed by roi number
    {root}/{n} (dataset): 2d uint8 image (n = str(roi_number))
    """
    with open_h5_group(hdf_file, group, replace=replace) as g:
        g.attrs['index'] = roifile.index
        # create image datasets and map them to roi numbers
        d = { n: g.create_dataset(str(n), data=im) for n, im in roifile.iteritems() }
        # now create sparse array of references keyed by roi number
        n = max(d.keys())+1
        r = [ d[i].ref if i in d else None for i in range(n) ]
        g.create_dataset('images', data=r, dtype=H5_REF_TYPE)

def hdr2hdf(hdr_dict, hdf_file, group=None, replace=True, archive=False):
    """hdr is represented as attributes on the group"""
    with open_h5_group(hdf_file, group, replace=replace) as root:
        for k, v in hdr_dict.items():
            root.attrs[k] = v

def file2hdf(hdf_root, ds_name, path, **kw):
    """write the contents of file (path) to open group (hdf_root)
    as dataset named (ds_name)"""
    with open(path,'rb') as infile:
        file_data = infile.read()
    file_array = bytearray(file_data)
    hdf_root.create_dataset(ds_name, data=file_array, **kw)

def hdf2file(hdf_dataset, path):
    file_data = bytearray(hdf_dataset)
    with open(path,'wb') as outfile:
        outfile.write(file_data)

def fileset2hdf(fileset, hdf_file, group=None, replace=True, archive=False):
    """fileset in HDF is
    {root}.pid (attribute) - full base pathname
    {root}.lid (attribute) - bin LID
    {root}.timestamp (attribute) - bin timestamp in ISO8601 UTC format
    {root}/hdr (group) - see hdr2hdf
    {root}/adc (group) - see adc2hdf
    {root}/roi (group) - see roi2hdf
    {root}/archive (group) - optional: archived files
    {root}/archive/adc (dataset) - archived ADC file
    {root}/archive/hdr (dataset) - archived HDR file
    """
    with open_h5_group(hdf_file, group, replace=replace) as root:
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
    with open_h5_group(hdf_path, group) as root:
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
    def __init__(self, group):
        self._group = group
    def iterkeys(self):
        for k in self._group.attrs['index']:
            yield k
    def __getitem__(self, roi_number):
        return np.array(self._group[self._group['images'][roi_number]])
        
class HdfBin(BaseBin, BaseDictlike):
    """Bin interface to HDF file/group.
    must be opened and closed with open/close or context manager interface
    """
    def __init__(self, hdf_file, group=None):
        self._hdf_file = hdf_file
        self._hdf_group = group
        self._group = None # for the open HDF file
        # context manager implementation
    def isopen(self):
        return self._group is not None
    def open(self, reopen=True):
        if self.isopen() and reopen:
            return self
        self._group = opengroup(self._hdf_file, self._hdf_group)
        return self
    def close(self, ignore_closed=False):
        if ignore_closed and not self.isopen():
            return
        self._group.close()
    def __enter__(self):
        return self.open()
    def __exit__(self, *args):
        self.close()
    # Dictlike
    @property
    @lru_cache()
    def csv(self):
        return h52df(self._group['adc'])
    @property
    @lru_cache()
    def schema(self):
        return SCHEMA[self._group['adc'].attrs['schema']]
    @lru_cache()
    def get_target(self, target_number):
        d = tuple(self.csv[c][target_number] for c in self.csv.columns)
        return d
    def __getitem__(self, target_number):
        return self.get_target(target_number)
    def iterkeys(self):
        for k in self.csv.index:
            yield k
    @property
    @lru_cache()
    def headers(self):
        return dict(self._group['hdr'].attrs)
    @property
    @lru_cache()
    def pid(self):
        return Pid(self._group.attrs['pid'])
    @property
    def images(self):
        return HdfRoi(self._group['roi'])
