"""
Support for stitching IFCB rev 1 images.
Does not infill; produces masked images where the mask indicates missing data.
"""
import numpy as np
from functools32 import lru_cache

from .utils import BaseDictlike

class Stitcher(BaseDictlike):
    """
    Delegate for Bins that stitches images.
    dictlike, with target numbers as keys and stitched images as values.
    """
    def __init__(self, the_bin):
        """
        :param the_bin: a back reference to the bin
        """
        self.bin = the_bin
    @property
    @lru_cache()
    def coordinates(self):
        S = self.bin.schema
        cols = [S.TRIGGER, S.ROI_X, S.ROI_Y, S.ROI_WIDTH, S.ROI_HEIGHT]
        # place adc image metrics data side by side with itself
        M = self.bin.adc[cols + cols]
        # naming of width and height column reflects future conversion to coordinates
        M.columns = ['at', 'ax1','ay1','ax2','ay2', 'bt', 'bx1','by1','bx2','by2']
        # exclude targets with width = 0 (i.e., with no ROI)
        M = M[M['ax2'] != 0]
        # now roll one side backwards to place adjacent pairs on same row
        M.iloc[:,5:] = np.roll(M.iloc[:,5:], -1, axis=0)
        # only consider pairs where trigger is the same
        M = M[M['at'] == M['bt']]
        # convert w/h to second corner coordinates
        M['ax2'] += M['ax1']
        M['ay2'] += M['ay1']
        M['bx2'] += M['bx1']
        M['by2'] += M['by1']
        # remove everything that doesn't overlap
        M = M[(M['ax1'] < M['bx2']) & \
              (M['ax2'] > M['bx1']) & \
              (M['ay1'] < M['by2']) & \
              (M['ay2'] > M['by1'])]
        # now compute stitched boxes
        M['sx1'] = np.minimum(M['ax1'], M['bx1'])
        M['sy1'] = np.minimum(M['ay1'], M['by1'])
        M['sx2'] = np.maximum(M['ax2'], M['bx2'])
        M['sy2'] = np.maximum(M['ay2'], M['by2'])
        return M
    def has_key(self, target_number):
        return target_number in self.coordinates.index
    def iterkeys(self):
        for k in self.coordinates.index:
            yield k
    @lru_cache(maxsize=2)
    def __getitem__(self, target_number):
        row = self.coordinates.loc[target_number]
        w = row['sx2'] - row['sx1']
        h = row['sy2'] - row['sy1']
        # create composite image
        msk = np.ones((h,w),dtype=np.bool)
        im = np.zeros((h,w),dtype=np.uint8)
        for ab,ij in zip('ab',[target_number, target_number+1]):
            rx1 = row[ab+'x1'] - row['sx1']
            ry1 = row[ab+'y1'] - row['sy1']
            rx2 = rx1 + row[ab+'x2'] - row[ab+'x1']
            ry2 = ry1 + row[ab+'y2'] - row[ab+'y1']
            msk[ry1:ry2,rx1:rx2] = False
            im[ry1:ry2,rx1:rx2] = self.bin.images[ij]
        return np.ma.array(im, mask=msk)
