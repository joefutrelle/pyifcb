import os
from contextlib import contextmanager
import tempfile
import shutil

import requests

from .identifiers import Pid
from .files import Fileset, FilesetBin

@contextmanager
def load_url(base_url):
    """
    Context manager for remote access to a bin. Stages
    files to a temporary directory and creates a ``FilesetBin``
    backed by them.

    :param url: the base URL of the remote files

    :Example:

    >>> with load_url('http://mysite.org/ifcb/D20170801T023142_IFCB113') as b:
    ...     im = b.images[32]


    """
    d = tempfile.mkdtemp()
    try:
        base_url = os.path.splitext(base_url)[0]
        base_path = os.path.join(d, Pid(base_url).bin_lid)
        for ext in ['hdr','adc','roi']:
            url = '%s.%s' % (base_url, ext)
            path = '%s.%s' % (base_path, ext)
            with open(path,'wb') as f:
                f.write(requests.get(url).content)
        fs = Fileset(base_path)
        yield FilesetBin(fs)
    finally:
        shutil.rmtree(d)
