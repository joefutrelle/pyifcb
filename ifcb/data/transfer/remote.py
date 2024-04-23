import os
import traceback
from collections import defaultdict

from smbclient import smbclient


DEFAULT_TIMEOUT = 30
DEFAULT_SHARE = 'Data'

class IfcbConnectionError(Exception):
    pass

def do_nothing(*args, **kw):
    pass

class RemoteIfcb(object):
    def __init__(self, addr, username, password, timeout=DEFAULT_TIMEOUT,
                    share=DEFAULT_SHARE, directory=''):
        self.addr = addr
        self.username = username
        self.password = password
        self.timeout = timeout
        self.share = share
        self.directory = directory
        self._c = None
    def open(self):
        smbclient.register_session(self.addr, self.username, self.password)
    def close(self):
        smbclient.delete_session(self.addr)
    def __enter__(self):
        self.open()
        return self
    def __exit__(self, type, value, traceback):
        self.close()
    def list_filesets(self):
        """list fileset lids, most recent first"""
        fs = defaultdict(lambda: 0)
        for fn in smbclient.listdir('\\'.join(['\\', self.addr, self.share, self.directory])):
            lid, ext = os.path.splitext(fn)
            if ext in ['.hdr','.roi','.adc']:
                fs[lid] += 1
        complete_sets = []
        for lid, c in fs.items():
            if c == 3: # complete fileset
                complete_sets.append(lid)
        return sorted(complete_sets, reverse=True)
    def transfer_fileset(self, lid, local_directory, skip_existing=True, create_directories=True):
        if create_directories:
            os.makedirs(local_directory, exist_ok=True)
        n_copied = 0
        for ext in ['hdr', 'adc', 'roi']:
            fn = '{}.{}'.format(lid, ext)
            local_path = os.path.join(local_directory, fn)
            remote_path = '\\'.join(['\\', self.addr, self.share, self.directory, fn])
            temp_local_path = local_path + '.temp_download'
            if skip_existing and os.path.exists(local_path):
                lf_size = os.path.getsize(local_path)
                stat = smbclient.stat(remote_path)
                rf_size = stat.st_size
                if lf_size == rf_size:
                    continue

            with smbclient.open_file(remote_path, 'rb') as fin:
                with open(temp_local_path, 'wb') as fout:
                    while True:
                        data = fin.read(1024)
                        if not data:
                            break
                        fout.write(data)

            os.rename(temp_local_path, local_path)
            n_copied += 1
        return n_copied > 0
    def delete_fileset(self, lid):
        #for ext in ['hdr', 'adc', 'roi']:
        #    self._c.deleteFiles(self.share, '{}.{}'.format(lid, ext))
        raise NotImplementedError()
    def sync(self, local_directory, progress_callback=do_nothing, fileset_callback=do_nothing):
        # local_directory can be
        # * a path, or
        # * a callbale returning a path when passed a bin lid
        fss = self.list_filesets()
        copied = []
        failed = []
        for lid in fss:
            print(lid)
            try:
                if callable(local_directory):
                    destination_directory = local_directory(lid)
                else:
                    destination_directory = local_directory
                was_copied = self.transfer_fileset(lid, destination_directory, skip_existing=True)
                if was_copied:
                    copied.append(lid)
                    fileset_callback(lid)
            except Exception as e:
                failed.append(lid)
                traceback.print_exc()
                pass
            progress_callback({
                'total': len(fss),
                'copied': copied,
                'failed': failed,
                'lid': lid
                })
