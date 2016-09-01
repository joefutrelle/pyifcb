import datetime

import numpy as np

from .h5utils import df2h5, open_h5_group, H5_REF_TYPE

def adc2hdf(adcfile, hdf_file, group=None, replace=True):
    """an ADC file is represented as a Pandas DataFrame"""
    with open_h5_group(hdf_file, group, replace=replace) as g:
        df2h5(g, adcfile.to_dataframe(), compression='gzip')

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
    with open_h5_group(hdf_file, group, replace=replace) as g:
        for k, v in hdr_dict.items():
            g.attrs[k] = v
        
def fileset2hdf(fileset, hdf_file, group=None, replace=True, archive=False):
    with open_h5_group(hdf_file, group, replace=replace) as root:
        root.attrs['lid'] = fileset.lid
        root.attrs['timestamp'] = fileset.timestamp.isoformat()
        hdr2hdf(fileset.hdr, root, 'hdr', replace=replace)
        adc2hdf(fileset.adc, root, 'adc', replace=replace)
        roi2hdf(fileset.roi, root, 'roi', replace=replace)
        if archive:
            with open(fileset.adc_path) as adcdata:
                root.create_dataset('archive/adc', data=np.array(adcdata.read()), compression='gzip')
            with open(fileset.hdr_path) as hdrdata:
                root.create_dataset('archive/hdr', data=np.array(hdrdata.read()), compression='gzip')
