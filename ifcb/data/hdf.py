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
    
def fileset2hdf(fileset, hdf_file, group=None, replace=True):
    with open_h5_group(hdf_file, group, replace=replace) as root:
        root.attrs['lid'] = fileset.lid
        root.attrs['timestamp'] = fileset.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        # hdr is an empty group with k/v pairs
        with open_h5_group(root, 'hdr', replace=replace) as hdr:
            for k, v in fileset.hdr.items():
                hdr.attrs[k] = v
        adc2hdf(fileset.adc, root, 'adc', replace=replace)
        roi2hdf(fileset.roi, root, 'roi', replace=replace)
