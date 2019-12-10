import re
import os

import pandas as pd

from scipy.io import loadmat

from ..identifiers import Pid
from ..utils import BaseDictlike
from .files import find_product_file, list_product_files

class ClassScoresDirectory(BaseDictlike):
    """a dictlike keyed by bin lid. the values are ClassScoresFiles"""
    def __init__(self, path, version=None, exhaustive=False):
        self.path = path
        if version is None:
            version = 1
        self.version = str(version)
        self.exhaustive = exhaustive
    def __getitem__(self, bin_lid):
        filename = '{}_class_v{}.mat'.format(bin_lid, self.version)
        year = Pid(bin_lid).timestamp.year
        likely_path = os.path.join(self.path, 'class{}_v{}'.format(year, self.version), filename)
        if os.path.exists(likely_path):
            return ClassScoresFile(likely_path, bin_lid, version=self.version)
        if self.exhaustive:
            path = find_product_file(self.path, filename, exhaustive=True)
            if path is not None:
                return ClassScoresFile(path, bin_lid, version=self.version)
        raise KeyError(bin_lid)
    def has_key(self, bin_lid):
        try:
            self[bin_lid]
            return True
        except KeyError:
            return False
    def keys(self):
        fn_regex = r'.*_class_v{}\.mat'.format(self.version)
        for p in list_product_files(self.path, fn_regex):
            # parse the filename as a pid
            bin_lid = Pid(os.path.basename(p)).bin_lid
            yield bin_lid
    def __repr__(self):
        return '<ClassScoresDirectory {}>'.format(self.path)

class ClassScoresFile(object):
    def __init__(self, path, bin_lid, version):
        self.path = path
        self.bin_lid = bin_lid
        self.version = version
    def class_scores(self):
        mat = loadmat(self.path, squeeze_me=True)
        roinum = mat['roinum']
        columns = mat['class2useTB'][:-1] # remove "unclassified"
        scores = mat["TBscores"]

        df = pd.DataFrame(scores, columns=columns)
        df = df.set_index(roinum)
        df.index.name = 'roi_number'

        return df