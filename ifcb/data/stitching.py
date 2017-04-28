"""
Support for stitching IFCB revision 1 images.
Note that this does not apply to data from commercial
IFCB instruments.
"""

import numpy as np
from functools import lru_cache

from .utils import BaseDictlike

class Stitcher(BaseDictlike):
    """
    Delegate for Bins that stitches images. Provides a
    dict-like interface, with target numbers as keys and
    stitched images as values.

    Stitched images are masked arrays with NaNs where image
    data is missing.
    """
    def __init__(self, the_bin):
        """
        :param the_bin: a back reference to the bin
        :type the_bin: Bin
        """
        self.bin = the_bin
    @property
    @lru_cache()
    def coordinates(self):
        """
        Compute stitched image metrics.

        :returns: stitched box coordinates of all stitched ROIs.
        """
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
        # bottom row is always spurious because of roll operation, remove
        M = M[:-1]
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
    @lru_cache()
    def excluded_targets(self):
        """
        Returns the target numbers of the targets that should
        be ignored in the original raw bin, because those targets
        are the second of a pair of stitched ROIs.

        This is just each included key + 1.
        """
        return [x + 1 for x in self.keys()]
    def has_key(self, target_number):
        """
        :returns bool: is the ROI with the given target
          number stitched?
        """
        return target_number in self.coordinates.index
    def keys(self):
        """
        Yield the target number of each stitched ROI.
        """
        for k in self.coordinates.index:
            yield k
    def __len__(self):
        return len(self.coordinates.index)
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

class Infiller(BaseDictlike):
    """
    Wraps ``Bin`` to perform infilling of stitched images.

    Provides dict-like interface; keys are target numbers,
    each value is a masked infill image that can be added to
    the raw stitched image to produce a complete image.

    Simply adding the raw stitch and infill images will fail
    by producing a completely masked image. Instead, use
    the InfilledImages utility class:
    following:

    >>> i = InfilledImages(my_bin)
    >>> infilled = i[target]

    which is equivalent to this:

    >>> s = Stitcher(my_bin)
    >>> i = Infiller(my_bin)
    >>> infilled = s[target].filled(0) + i[target].filled(0)

    """
    def __init__(self, the_bin):
        """
        :param the_bin: the bin to delegate to
        :type the_bin: Bin
        """
        self.stitcher = Stitcher(the_bin)
    def keys(self):
        """
        Yield the target number of each stitched ROI.
        """
        for k in self.stitcher:
            yield k
    def has_key(self, target_number):
        """
        :returns bool: is the ROI with the given target
          number stitched?
        """
        return target_number in self.stitcher
    def __getitem__(self, target_number):
        # get the raw stitch
        raw_stitch = self.stitcher[target_number]
        # compute the fill value (median of pixel values)
        fill_value = np.ma.median(raw_stitch)
        # construct an image containing the fill value
        fill_image = np.full(raw_stitch.shape, dtype=np.uint8, fill_value=fill_value)
        # now return the masked version of that image
        return np.ma.array(fill_image, mask=np.logical_not(raw_stitch.mask))

class InfilledImages(BaseDictlike):
    """
    Wraps a bin's "images" property and provides access to infilled
    images. Images that are not infilled are passed through.

    Dict-like interface excludes from its keys target numbers that
    refer to the second ROI in a stitched pair.
    """
    def __init__(self, the_bin):
        self.bin = the_bin
        self.stitcher = Stitcher(the_bin)
        self.infiller = Infiller(the_bin)
    def keys(self):
        """
        Yield the target number of each ROI that is not the second
        ROI in a stitched pair.
        """
        for k in self.bin.images:
            if k not in self.stitcher.excluded_targets():
                yield k
    def has_key(self, target_number):
        """
        Exclude each target number from the bin's images that is
        second ROI from a stitched pair.
        """
        in_bin = target_number in self.bin
        excluded = target_number in self.stitcher.excluded_targets()
        return in_bin and not excluded
    def __getitem__(self, target_number):
        if target_number in self.stitcher:
            # stitch the images
            raw_stitch = self.stitcher[target_number]
            # construct infill
            infill = self.infiller[target_number]
            # sum the stitched and infill images
            return raw_stitch.filled(0) + infill.filled(0)
        else:
            # this is not a stitched image
            return self.bin.images[target_number]
