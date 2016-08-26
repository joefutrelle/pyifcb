import numpy as np
import pandas as pd
import h5py as h5

def touch_group(h5group, group_path):
    """ensure that an h5 Group exists at the given path.
    returns the group"""
    try:
        return h5group.create_group(group_path)
    except ValueError:
        # the following must succeed
        return h5group.get(group_path)
    
def df2h5(h5group, df, compression=None, replace=True):
    """save a pandas dataframe to hdf5 including a special "columns" attribute
    that contains column names in order. this is different from pandas.to_hdf, less efficient
    for dataframes with a uniform dtype, but has reasonable naming conventions.
    parameters:
    h5group - an h5py Group object in which to store the dataframe,
    df - the dataframe,
    compression - optional compression type"""
    for c in df.columns:
        if replace and c in h5group:
            del h5group[c]
        h5group.create_dataset(c, data=df[c], compression=compression)
    h5group.attrs.create('columns', data=df.columns, dtype=h5.special_dtype(vlen=bytes))
        
def h52df(h5group):
    """read a pandas dataframe from hdf5 represented as a group where each
    key is a column. looks for a "columns" attribute giving the column names
    in order, but doesn't require it.
    parameters:
    h5group an h5py Group object in which the dataframe is stored"""
    # note that the DataFrame constructor ignores h5py Group objects
    d = dict(h5group)
    try:
        cols = np.array(h5group.attrs['columns'])
        return pd.DataFrame(d, columns=cols)
    except KeyError:
        return pd.DataFrame(d)
