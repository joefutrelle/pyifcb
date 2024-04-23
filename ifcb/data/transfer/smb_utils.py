import sys
import os
import logging
from contextlib import contextmanager
import traceback

import smbclient

DEFAULT_TIMEOUT=30

def split_path(path):
    dirname, last_name = os.path.split(path)
    if not dirname or dirname == '/':
        return [last_name]
    else:
        return split_path(dirname) + [last_name]

def share_name(path):
    return split_path(path)[0]

def path_on_share(path):
    sp = split_path(path)
    if len(sp) == 1:
        return ''
    else:
        return os.path.join(*sp[1:])

# list local directory
def list_local_directory(path):
    return os.listdir(path)


def smb_connect(remote_server, username, password):

    smbclient.register_session(remote_server, username, password)

    return smbclient


@contextmanager
def smb_connection(remote_server, username, password):
    c = smb_connect(remote_server, username, password)

    try:
        yield c
    except:
        traceback.print_exc()

def do_nothing(*args, **kw):
    pass

def progress(total_files, n_copied, fn):
    return {
        'total': total_files,
        'copied': n_copied,
        'filename': fn,
    }
