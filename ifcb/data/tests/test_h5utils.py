import unittest
import os
from contextlib import contextmanager

import numpy as np
import h5py as h5
import pandas as pd

from pandas.util.testing import assert_frame_equal

from ifcb.tests.utils import withfile

from ..h5utils import open_h5_group, clear_h5_group, df2h5, h52df

class TestH5Utils(unittest.TestCase):
    @withfile
    def test_open_h5_group(self, F):
        attr = 'test'
        v1, v2 = 5, 6
        for group in [None, 'g']:
            with open_h5_group(F, group, replace=True) as f:
                f.attrs[attr] = v1
            assert os.path.exists(F)
            with open_h5_group(F, group) as f:
                assert f.attrs[attr] == v1
            with open_h5_group(F, group, replace=True) as f:
                f.attrs[attr] = v2
            with open_h5_group(F, group) as f:
                assert f.attrs[attr] == v2
    @withfile
    def test_clear_h5_group(self, F):
        with h5.File(F) as f:
            f['foo/bar'] = [1,2,3]
            f.attrs['baz'] = 5
        with h5.File(F) as f:
            assert 'foo' in f.keys()
            assert 'baz' in f.attrs.keys()
            clear_h5_group(f)
        with h5.File(F) as f:
            assert not f.keys()
            assert not f.attrs.keys()
    @withfile
    def test_df_h5_roundtrip(self, F):
        r = np.random.RandomState(0) # seed
        data = r.normal(size=(5,3))
        in_df = pd.DataFrame(data=data)
        @contextmanager
        def roundtrip(): # test dataframe roundtrip
            with open_h5_group(F,replace=True) as g:
                yield in_df
                df2h5(g, in_df)
                out_df = h52df(g)
                assert_frame_equal(in_df, out_df, check_index_type='equiv', check_column_type='equiv')
        with roundtrip():
            in_df.index = r.permutation(in_df.index)
        with roundtrip():
            in_df.columns = ['col%d' % n for n in range(len(in_df.columns))]
        with roundtrip():
            in_df['new_col'] = np.arange(len(in_df)) # different type column
        with roundtrip():
            in_df.index.name = 'hello'
