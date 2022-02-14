import re
import os

import pandas as pd
import h5py as h5
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
        self.version = version
        self.exhaustive = exhaustive
    def _get_v1_file(self, bin_lid):
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
    def _get_v2_file(self, bin_lid):
        filename = '{}_class_v2.h5'.format(bin_lid)
        path = find_product_file(self.path, filename, exhaustive=self.exhaustive)
        if path is not None:
            return ClassScoresFile(path, bin_lid, version=2)
        raise KeyError(bin_lid)
    def _get_v3_file(self, bin_lid):
        filename = '{}_class.h5'.format(bin_lid)
        # support certain IFCB classifier output
        pid = Pid(bin_lid)
        year = pid.timestamp.year
        doy = f'{pid.timestamp.dayofyear:03d}'
        possible_path = os.path.join(self.path, f'D{year}', f'D{year}_{doy}', filename)
        if os.path.exists(possible_path):
            path = possible_path
        else:
            # this is the most likely case
            path = find_product_file(self.path, filename, exhaustive=self.exhaustive)
        if path is not None:
            return ClassScoresFile(path, bin_lid, version=3)
        raise KeyError(bin_lid)
    def __getitem__(self, bin_lid):
        if self.version == 1:
            return self._get_v1_file(bin_lid)
        elif self.version == 2:
            return self._get_v2_file(bin_lid)
        elif self.version == 3:
            return self._get_v3_file(bin_lid)
        else:
            raise KeyError('unknown class scores version {}'.format(version))
    def has_key(self, bin_lid):
        try:
            self[bin_lid]
            return True
        except KeyError:
            return False
    def keys(self):
        if self.version == 1:
            fn_regex = r'.*_class_v1\.mat'
        elif self.version == 2:
            fn_regex = r'.*_class_v2\.h5'
        elif self.version == 3:
            fn_regex = r'.*_class.h5'
        for p in list_product_files(self.path, fn_regex):
            # parse the filename as a pid
            bin_lid = Pid(os.path.basename(p)).bin_lid
            yield bin_lid
    def __repr__(self):
        return '<ClassScoresDirectory {} v{}>'.format(self.path, self.version)

class ClassScoresFile(object):
    def __init__(self, path, bin_lid, version):
        self.path = path
        self.bin_lid = bin_lid
        self.version = version
    def _cs2df(self, scores, class_labels, roi_numbers):
        df = pd.DataFrame(scores, columns=class_labels)
        df = df.set_index(roi_numbers)
        df.index.name = 'roi_number' 
        return df       
    def _class_scores_v1(self):
        mat = loadmat(self.path, squeeze_me=True)
        roi_numbers = mat['roinum']
        class_labels = mat['class2useTB'][:-1] # remove "unclassified"
        scores = mat["TBscores"]
        return self._cs2df(scores, class_labels, roi_numbers)
    def _class_scores_v2(self):
        with h5.File(self.path, 'r') as f:
            ds = f['scores']
            scores = ds[:]
            class_labels = [l.decode('ascii') for l in ds.attrs['class_labels']]
            roi_numbers = f['roi_numbers'][:]
        return self._cs2df(scores, class_labels, roi_numbers)
    def _class_scores_v3(self):
        with h5.File(self.path, 'r') as f:
            ds = f['output_scores']
            scores = ds[:]
            class_labels = [l.decode('ascii') for l in f['class_labels'][:]]
            roi_numbers = f['roi_numbers'][:]
        return self._cs2df(scores, class_labels, roi_numbers)
    def class_scores(self):
        if self.version == 1:
            return self._class_scores_v1()
        elif self.version == 2:
            return self._class_scores_v2()
        elif self.version == 3:
            return self._class_scores_v3()
        else:
            raise KeyError('unknown class scores version {}'.format(self.version))
