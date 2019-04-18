import re
import os
from zipfile import ZipFile
from io import BytesIO

from ..identifiers import Pid
from ..utils import BaseDictlike
from ..imageio import read_image
from .files import find_product_file, list_product_files

class BlobDirectory(BaseDictlike):
    """a dictlike keyed by bin lid. the values are BlobFiles"""
    def __init__(self, path, version='2'):
        self.path = path
        self.version = version
    def __getitem__(self, bin_lid):
        filename = '{}_blobs_v{}.zip'.format(bin_lid, self.version)
        # note that versions other than 2 might not be zip files
        path = find_product_file(self.path, filename)
        if path is not None:
            return BlobFile(path, bin_lid, version=self.version)
        raise KeyError(bin_lid)
    def has_key(self, bin_lid):
        try:
            self[bin_lid]
            return True
        except KeyError:
            return False
    def keys(self):
        fn_regex = '.*_blobs_v.*'
        for p in list_product_files(self.path, fn_regex):
            # parse the filename as a pid
            bin_lid = Pid(os.path.basename(p)).bin_lid
            yield BlobFile(p, bin_lid, version=self.version)
    def __str__(self):
        return '<BlobDirectory {}>'.format(self.path)

class BlobFile(BaseDictlike):
    def __init__(self, path, bin_lid, version='2'):
        self.path = path
        self.bin_lid = bin_lid
        self._zipfile = None
    def open(self):
        if self._zipfile is None:
            self._zipfile = ZipFile(self.path)
    def close(self):      
        if self._zipfile is not None:
            self._zipfile.close()
    def __enter__(self):
        self.open()
    def __exit__(self, *args):
        self.close()
    def _read_image(self, zin, target_number):
        entry_name = '{}_{:05d}.png'.format(self.bin_lid, target_number)
        return BytesIO(zin.read(entry_name))
    def __getitem__(self, target_number):
        if self._zipfile is None:
            with ZipFile(self.path) as zin:
                image_data = self._read_image(zin, target_number)
        else:
            image_data = self._read_image(self._zipfile, target_number)
        return read_image(image_data)
    def _keys(self, zin):
        for name in zin.namelist():
            if re.match(r'.*\.png$', name):
                 yield int(Pid(name).target)
    def keys(self):
        if self._zipfile is None:
            with ZipFile(self.path) as zin:
                yield from self._keys(zin)
        else:
            yield from self._keys(self._zipfile)
    def __str__(self):
        return '<BlobFile {}>'.format(self.bin_lid)

