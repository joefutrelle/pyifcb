import os
import sys

import numpy as np

from ifcb import DataDirectory

TEST_DATA_DIR=os.path.join('ifcb','tests','data','test_data')

WHITELIST = ['data','white']

TEST_FILES = {
    'D20130526T095207_IFCB013': {
        'n_rois': 19,
        'n_targets': 118,
        'roi_numbers': [7, 11, 13, 21, 32, 33, 47, 49, 54, 61, 66, 68, 73, 78, 80, 92, 99, 102, 114],
        'roi_number': 99,
        'roi_shape': (34, 64),
        'roi_slice_coords': [slice(0,5), slice(0,5)],
        'roi_slice': np.array([[172, 168, 172, 166, 171],
                               [168, 170, 172, 171, 170],
                               [167, 174, 171, 175, 168],
                               [173, 171, 173, 170, 171],
                               [176, 169, 176, 173, 172]], dtype=np.uint8),
        'sizes': {
            'roi': 98472,
            'hdr': 2885,
            'adc': 19395
        },
        'headers': {
            'KloehnPort': 'COM3',
            'laserMotorSmallStep_ms': 1000,
            'blobXgrowAmount': 20
        }
    },
    'IFCB5_2012_028_081515': {
        'n_rois': 6,
        'n_targets': 7,
        'roi_numbers': [1, 2, 3, 4, 5, 6],
        'roi_number': 1,
        'roi_shape': (45, 96),
        'roi_slice_coords': [slice(0,5), slice(0,5)],
        'roi_slice': np.array([[208, 207, 206, 206, 207],
                               [206, 206, 206, 207, 206],
                               [206, 207, 205, 206, 208],
                               [208, 208, 208, 208, 209],
                               [206, 206, 205, 207, 207]], dtype=np.uint8),
        'stitched_roi_number': 3,
        'roi_numbers_stitched': [1, 2, 3, 5, 6],
        'stitched_roi_shape': (86, 263),
        'stitched_roi_coords': [slice(23,27), slice(177,183)],
        'stitched_roi_slice': np.array([[205, 204, 205, 0, 0, 0],
                                        [202, 203, 206, 0, 0, 0],
                                        [205, 206, 205, 204, 202, 202],
                                        [204, 202, 205, 203, 202, 204]], dtype=np.uint8),
        'stitched_corners': {1: [208, 204, 205, 205],
                             2: [205, 199, 203, 197],
                             3: [210, 203, 207, 203],
                             5: [210, 209, 212, 209],
                             6: [212, 206, 209, 208]},
        'sizes': {
            'roi': 71083,
            'hdr': 301,
            'adc': 1004
        },
        'headers': {
            'binarizeThreshold': 30,
            'fluorescencePhotomultiplierSetting': 0.6,
        }
    }
}

def data_dir():
    for p in sys.path:
        fp = os.path.join(p, TEST_DATA_DIR)
        if os.path.exists(fp):
            return fp
    raise KeyError('cannot find %s on sys.path' % TEST_DATA_DIR)

def _dd():
    return DataDirectory(data_dir(), whitelist=WHITELIST)

def get_fileset_bin(lid):
    return _dd()[lid]

def list_test_bins():
    return list(_dd())
    
def list_test_filesets():
    return [b.fileset for b in list_test_bins()]
