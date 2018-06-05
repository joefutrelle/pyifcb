import os

from .smb_utils import smb_connect

DEFAULT_TIMEOUT = 30
DEFAULT_SHARE = 'data'

class RemoteIfcb(object):
    def __init__(self, addr, username, password, timeout=DEFAULT_TIMEOUT):
        self.addr = addr
        self.username = username
        self.password = password
        self.timeout = timeout
        self.share = DEFAULT_SHARE
    def __enter__(self):
        self._c = smb_connect(self.addr, self.username, self.password, self.timeout)
        return self
    def __exit__(self, type, value, traceback):
        try:
            self._c.close()
        except:
            pass
    def list_filesets(self):
        """list fileset lids, most recent first"""
        fs = []
        for f in self._c.listPath(self.share, ''):
            if f.isDirectory:
                continue
            fn = f.filename
            if fn.endswith('.hdr'):
                fs.append(fn[:-4])
        return sorted(fs, reverse=True)
    def transfer_fileset(self, lid, local_directory, skip_existing=True):
        for ext in ['hdr', 'adc', 'roi']:
            fn = '{}.{}'.format(lid, ext)
            local_path = os.path.join(local_directory, fn)
            remote_path = fn
            temp_local_path = local_path + '.temp_download'

            if skip_existing and os.path.exists(local_path):
                lf_size = os.path.getsize(local_path)
                rf = self._c.getAttributes(self.share, remote_path)
                if lf_size == rf.file_size:
                    continue

            with open(temp_local_path, 'wb') as fout:
                self._c.retrieveFile(self.share, remote_path, fout)
            os.rename(temp_local_path, local_path)
