import re
import os

import pandas as pd

from ..identifiers import Pid
from ..utils import BaseDictlike
from .files import find_product_file, list_product_files

class FeaturesDirectory(BaseDictlike):
    """a dictlike keyed by bin lid. the values are FeaturesFiles"""
    def __init__(self, path, version=None):
        self.path = path
        if version is None:
            version = 2
        self.version = int(version)
    def __getitem__(self, bin_lid):
        year = Pid(bin_lid).year
        filename = '{}_fea_v{}.csv'.format(bin_lid, self.version)
        # legacy refers to v2 features
        if self.version == 2:
            legacy_dir = 'features{}_v{}'.format(year, self.version)
            legacy_path = os.path.join(self.path, legacy_dir, filename)
            if os.path.exists(legacy_path):
                return FeaturesFile(legacy_path, bin_lid, version=self.version)
            if os.path.exists(os.path.join(self.path, legacy_dir)): # the legacy dir is there, but not the features file
                # avoid searching massive directories
                raise KeyError(bin_lid)
        path = find_product_file(self.path, filename, exhaustive=True)
        if path is not None:
            return FeaturesFile(path, bin_lid, version=self.version)
        raise KeyError(bin_lid)
    def has_key(self, bin_lid):
        try:
            self[bin_lid]
            return True
        except KeyError:
            return False
    def keys(self):
        fn_regex = r'.*_fea_v{}\.csv'.format(self.version)
        for p in list_product_files(self.path, fn_regex):
            # parse the filename as a pid
            bin_lid = Pid(os.path.basename(p)).bin_lid
            yield bin_lid
    def __repr__(self):
        return '<FeaturesDirectory {}>'.format(self.path)

class FeaturesFile(object):
    def __init__(self, path, bin_lid, version):
        self.path = path
        self.bin_lid = bin_lid
        self.version = version
    def features(self, prune=False):
        # prune removes features not useful for plotting
        df = pd.read_csv(self.path, index_col='roi_number')
        if prune:
            for c in df.columns:
                if re.match(r'(Ring|Wedge|HOG)\d+',c):
                    df.pop(c)
        return df
    def __repr__(self):
        return '<FeaturesFile {}>'.format(self.bin_lid)
