from functools import lru_cache

from rectpack import newPacker, SORT_AREA
from rectpack.guillotine import GuillotineBafSlas

import numpy as np
import pandas as pd

from ifcb.data.stitching import InfilledImages

class Mosaic(object):
    def __init__(self, the_bin, shape=(720, 1280), bg_color=200):
        self.bin = the_bin
        self.shape = shape
        self.bg_color = bg_color
        self.ii = InfilledImages(self.bin)
    @lru_cache()
    def _shapes(self):
        hs, ws, ix = [], [], []
        for target_number in self.ii:
            h, w = self.ii.shape(target_number)
            hs.append(h)
            ws.append(w)
            ix.append(target_number)
        return zip(hs, ws, ix)
    @lru_cache()
    def _pack(self):
        page_h, page_w = self.shape
        pages = [(page_h - 1, page_w - 1) for _ in range(20)]
        packer = newPacker(sort_algo=SORT_AREA, rotation=False, pack_algo=GuillotineBafSlas)
        for r in self._shapes():
            packer.add_rect(*r)
        for p in pages:
            packer.add_bin(*p)
        packer.pack()
        COLS = ['page', 'y', 'x', 'h', 'w', 'roi_number']
        return pd.DataFrame(packer.rect_list(), columns=COLS)
    def page(self, page=0):
        df = self._pack()
        page_h, page_w = self.shape
        page_image = np.zeros((page_h, page_w), dtype=np.uint8) + self.bg_color
        sdf = df[df.page == page]
        for index, row in sdf.iterrows():
            y, x = row.y, row.x
            h, w = row.h, row.w
            page_image[y:y+h, x:x+w] = self.ii[row.roi_number]
        return page_image