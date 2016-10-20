import os
from contextlib import contextmanager
import tempfile
import shutil

import requests

from .identifiers import Pid
from .files import Fileset, FilesetBin

@contextmanager
def remote_bin(base_url):
    base_url = os.path.splitext(base_url)[0]
    d = tempfile.mkdtemp()
    base_path = os.path.join(d, Pid(base_url).bin_lid)
    try:
        for ext in ['hdr','adc','roi']:
            url = '%s.%s' % (base_url, ext)
            path = '%s.%s' % (base_path, ext)
            with open(path,'wb') as f:
                f.write(requests.get(url).content)
        fs = Fileset(base_path)
        yield FilesetBin(fs)
    finally:
        shutil.rmtree(d)
