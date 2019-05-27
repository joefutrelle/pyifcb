from functools import lru_cache
import math

from skimage.transform import resize

from rectpack import newPacker, SORT_AREA
from rectpack.guillotine import GuillotineBafSlas

import numpy as np
import pandas as pd

from ifcb.data.stitching import InfilledImages

class Mosaic(object):
    def __init__(self, the_bin, shape=(600, 800), scale=0.33, bg_color=200, coordinates=None):
        self.bin = the_bin
        self.shape = shape
        self.bg_color = bg_color
        self.scale = scale
        self.coordinates = coordinates
    @lru_cache()
    def _shapes(self):
        hs, ws, ix = [], [], []
        with self.bin:
            ii = InfilledImages(self.bin)
            for target_number in ii:
                h, w = ii.shape(target_number)
                hs.append(math.floor(h * self.scale))
                ws.append(math.floor(w * self.scale))
                ix.append(target_number)
        return zip(hs, ws, ix)
    def pack(self, max_pages=20):
        if self.coordinates is not None:
            return self.coordinates
        page_h, page_w = self.shape
        pages = [(page_h - 1, page_w - 1) for _ in range(max_pages)]
        packer = newPacker(sort_algo=SORT_AREA, rotation=False, pack_algo=GuillotineBafSlas)
        for r in self._shapes():
            packer.add_rect(*r)
        for p in pages:
            packer.add_bin(*p)
        packer.pack()
        COLS = ['page', 'y', 'x', 'h', 'w', 'roi_number']
        self.coordinates = pd.DataFrame(packer.rect_list(), columns=COLS)
        return self.coordinates
    def page(self, page=0):
        df = self.pack()
        page_h, page_w = self.shape
        page_image = np.zeros((page_h, page_w), dtype=np.uint8) + self.bg_color
        sdf = df[df.page == page]
        with self.bin:
            ii = InfilledImages(self.bin)
            for index, row in sdf.iterrows():
                y, x = row.y, row.x
                h, w = row.h, row.w
                unscaled_image = ii[row.roi_number]
                scaled_image = resize(unscaled_image, (h, w), mode='reflect', preserve_range=True)
                page_image[y:y+h, x:x+w] = scaled_image
        return page_image