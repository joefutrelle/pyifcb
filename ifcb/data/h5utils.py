import numpy as np
import pandas as pd
import h5py as h5

def df2h5(h5group, df, replace=False, **kw):
    """write a pandas dataframe to hdf5 represented as a group containing
    data: column data, keyed by column name
    index: dataframe index
    columns: list of column names
    non-string column names will be coerced to strings and so will not
    round-trip.
    parameters:
    h5group - an h5py Group object in which to store the dataframe,
    df - the dataframe"""
    if replace:
        for k in h5group.keys(): del h5group[k]
        for k in h5group.attrs.keys(): del h5group.attrs[k]
    data = h5group.create_group('data')
    cols = map(str,df.columns)
    for c,n in zip(df.columns, cols):
        data.create_dataset(n, data=df[c], **kw)
    h5group.create_dataset('index', data=df.index, **kw)
    h5group.create_dataset('columns', data=cols, dtype=h5.special_dtype(vlen=bytes), **kw)

def h52df(h5group):
    """read a pandas dataframe from hdf5 represented as a group containing
    data: column data, keyed by column name
    index: dataframe index
    columns: list of column names
    parameters:
    h5group an h5py Group object in which the dataframe is stored"""
    d = dict(h5group.get('data'))
    try:
        cols = np.array(h5group['columns'])
    except KeyError:
        cols = None
    try:
        index = np.array(h5group['index'])
    except KeyError:
        index = None
    return pd.DataFrame(d, columns=cols, index=index)
