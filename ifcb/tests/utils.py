import os
import shutil
import tempfile
from contextlib import contextmanager

@contextmanager
def test_dir():
    """context mgr for tempdir; not sure
    why this isn't part of tempfile"""
    d = tempfile.mkdtemp()
    try:
        yield d
    finally:
        shutil.rmtree(d)
    
