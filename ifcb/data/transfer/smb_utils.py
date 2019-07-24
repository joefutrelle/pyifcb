import sys
import os
import logging
from contextlib import contextmanager
import traceback

from smb.SMBConnection import SMBConnection
from nmb.NetBIOS import NetBIOS

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

class NameError(Exception):
    pass

def get_netbios_name(remote_addr, timeout=DEFAULT_TIMEOUT):
    nb = NetBIOS()
    names = nb.queryIPForName(remote_addr, timeout=timeout)
    nb.close()
    if names is None or len(names) == 0:
        raise NameError('No NetBIOS name found for {}'.format(remote_addr))
    elif len(names) > 1:
        logging.warn('More than one NetBIOS name for {}'.format(remote_addr))
    return names[0]

def smb_connect(remote_server, username, password, timeout=DEFAULT_TIMEOUT):

    logging.debug('Querying NetBIOS for name of {}'.format(remote_server))
    remote_name = get_netbios_name(remote_server, timeout=timeout)
    logging.debug('Name is {}'.format(remote_name))

    logging.debug('Connecting to {}'.format(remote_server))

    c = SMBConnection(username, password, 'ignore', remote_name)
    c.connect(remote_server, timeout=timeout)

    return c

@contextmanager
def smb_connection(remote_server, username, password, timeout=DEFAULT_TIMEOUT):
    c = smb_connect(remote_server, username, password, timeout)

    try:
        yield c
    except:
        traceback.print_exc()
    finally:
        logging.debug('Closing connection to {}'.format(remote_server))

        c.close()

def smb_sync_directory(remote_server, username, password, remote_path, local_path,
    timeout=DEFAULT_TIMEOUT, limit=None):
    """copies a remote directory to a local one (non-recursive).
    remote_server = remote server DNS name or IP address
    username = Samba username on remote server
    password = Samba username's password on remote server
    remote_path = path to remote directory including share name (e.g., '/some_share/some/folder')
    local_path = path to local directory
    will only transfer files that are 1) not in the local directory, or
    2) are a different size than the one in the local directory.
    Does not recurse into subdirectories."""
    local_files = list_local_directory(local_path)

    n_copied = 0

    with smb_connection(remote_server, username, password, timeout=timeout) as c:
        logging.debug('listing remote directory {}'.format(remote_path))

        share = share_name(remote_path)
        pos = path_on_share(remote_path)
        remote_files = [f for f in c.listPath(share, pos) if not f.isDirectory]

        def safe_copy_file(remote_file, local_file):
            logging.debug('Copying {} to {}'.format(remote_file.filename, local_file))
            download_path = local_file + '.temp_download'
            remote_path = os.path.join(pos, remote_file.filename)

            try:
                with open(download_path,'wb') as fout:
                    c.retrieveFile(share, remote_path, fout)
                os.rename(download_path, local_file)
                return True
            except:
                return False
            finally:
                # clean up
                if os.path.exists(download_path):
                    os.remove(download_path)

        for rf in remote_files:
            if limit is not None and n_copied == limit:
                return

            name = rf.filename
            local_file = os.path.join(local_path, name)
            try:
                if name not in local_files:
                    logging.debug('{} does not exist locally'.format(name))
                    if safe_copy_file(rf, local_file):
                        n_copied += 1
                else:
                    remote_size = rf.file_size
                    local_size = os.path.getsize(local_file)
                    if local_size != remote_size:
                        logging.debug('remote file {} is not the same size as local copy'.format(name))
                        if safe_copy_file(rf, local_file):
                            n_copied += 1
            except:
                traceback.print_exc()
                # move on to next file