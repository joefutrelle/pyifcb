from .h5utils import df2h5, open_h5_group

def adc2hdf(adcfile, hdf_file, group=None, replace=True, **kw):
    kw.update({'compression':'gzip'}) # always compress ADC data
    with open_h5_group(hdf_file, group, replace=replace) as g:
        df2h5(g, adcfile.to_dataframe(), replace=replace, **kw)

def roi2hdf(roifile, hdf_file, group=None, replace=True, **kw):
    kw.update({'compression':None}) # never compress ROI data
    with open_h5_group(hdf_file, group, replace=replace) as g:
        g.attrs['index'] = roifile.index
        for roi_number, image in roifile.iteritems():
            key = str(roi_number)
            g.create_dataset(key, data=image, **kw)
    
def fileset2hdf(fileset, hdf_file, group=None, replace=True):
    with open_h5_group(hdf_file, group, replace=replace) as root:
        root.attrs['lid'] = fileset.lid
        root.attrs['timestamp'] = fileset.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        with open_h5_group(root, 'hdr', replace=replace) as hdr:
            for k, v in fileset.hdr.items():
                hdr.attrs[k] = v
        adc2hdf(fileset.adc, root, 'adc', replace=replace)
        roi2hdf(fileset.roi, root, 'roi', replace=replace)
