"""
Convenience utilities for ``h5py``.
"""

from contextlib import contextmanager

import numpy as np
import pandas as pd
import h5py as h5

H5_REF_TYPE = h5.special_dtype(ref=h5.Reference)

def clear_h5_group(h5group):
    """
    Delete all keys and attrs from an ``h5py.Group``.

    :param h5group: the h5py.Group
    """
    for k in h5group.keys(): del h5group[k]
    for k in h5group.attrs.keys(): del h5group.attrs[k]

class hdfopen(object):
    """
    Context manager that opens an ``h5py.Group`` from an ``h5py.File``
    or other group.

    Parameters:

    * path - path to HDF5 file, or open HDF5 group
    * group - for HDF5 file paths, the path of the group to return (optional)
      for groups, a subgroup to require (optional)
    * replace - whether to replace any existing data

    :Example:

    >>> with hdfopen('myfile.h5','somegroup') as g:
    ...     g.attrs['my_attr'] = 3

    """
    def __init__(self, path, group=None, replace=None):
        if isinstance(path, h5.Group):
            if group is not None:
                self.group = path.require_group(group)
            else:
                self.group = path
            if replace:
                clear_h5_group(self.group)
            self._file = None
        else:
            mode = 'w' if replace else 'r+'
            self._file = h5.File(path, mode)
            if group is not None:
                self.group = self._file.require_group(group)
            else:
                self.group = self._file
    def close(self):
        if self._file is not None:
            self._file.close()
    def __enter__(self, *args, **kw):
        return self.group
    def __exit__(self, *args):
        self.close()
        pass

def pd2hdf(group, df, **kw):
    """
    Write ``pandas.DataFrame`` to HDF5 file. This differs
    from pandas's own HDF5 support by providing a slightly less
    optimized but easier-to-access format. Passes keywords
    through to each ``h5py.create_dataset`` operation.

    Layout of Pandas ``DataFrame`` / ``Series`` representation:

    * ``{path}`` (group): the group containing the dataframe
    * ``{path}.ptype`` (attribute): '``DataFrame``'
    * ``{path}/columns`` (dataset): 1d array of references to column data
    * ``{path}/columns.names`` (attribute, optional): 1d array of column names
    * ``{path}/{n}`` (dataset): 1d array of data for column n
    * ``{path}/index`` (dataset): 1d array of data for dataframe index
    * ``{path}/index.name`` (attribute, optional): name of index

    :param group: the ``h5py.Group`` to write the ``DataFrame`` to
    """
    group.attrs['ptype'] = 'DataFrame'
    refs = []
    for i in range(len(df.columns)):
        c = group.create_dataset(str(i), data=df.iloc[:,i], **kw)
        refs.append(c.ref)
    cols = group.create_dataset('columns', data=refs, dtype=H5_REF_TYPE)
    if df.columns.dtype == np.int64:
        cols.attrs['names'] = [int(col) for col in df.columns]
    else:
        cols.attrs['names'] = [str(str(col).encode('utf8')) for col in df.columns]
    ix = group.create_dataset('index', data=df.index, **kw)
    if df.index.name is not None:
        ix.attrs['name'] = df.index.name

def hdf2pd(group):
    """
    Read a ``pandas.DataFrame`` from an ``h5py.Group``.

    :param group: the ``h5py.Group`` to read from.
    """
    if group.attrs['ptype'] != 'DataFrame':
        raise ValueError('unrecognized HDF format')
    index = group['index']
    index_name = index.attrs.get('name',None)
    col_refs = group['columns']
    col_data = [np.array(group[r]) for r in col_refs]
    # note: the below assumes that no column names mean use numeric oness
    col_names = col_refs.attrs.get('names', range(len(col_refs)))
    data = { k: v for k, v in zip(col_names, col_data) }
    index = pd.Series(index, name=index_name)
    return pd.DataFrame(data=data, index=index, columns=col_names)
