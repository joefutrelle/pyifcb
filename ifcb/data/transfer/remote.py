import os

from collections import defaultdict

from .smb_utils import smb_connect, get_netbios_name, NameError
from smb.base import SharedDevice

DEFAULT_TIMEOUT = 30
DEFAULT_SHARE = 'data'

class IfcbConnectionError(Exception):
    pass

def do_nothing(*args, **kw):
    pass

class RemoteIfcb(object):
    def __init__(self, addr, username, password, timeout=DEFAULT_TIMEOUT,
                    share=DEFAULT_SHARE, connect=True):
        self.addr = addr
        self.username = username
        self.password = password
        self.timeout = timeout
        self.share = share
        self.connect = connect
        self._c = None
    def open(self):
        if self._c is not None:
            return
        try:
            self._c = smb_connect(self.addr, self.username, self.password, self.timeout)
        except:
            raise IfcbConnectionError('unable to connect to IFCB')
    def close(self):
        if self._c is not None:
            self._c.close()
            self._c = None
    def __enter__(self):
        if self.connect:
            self.open()
        return self
    def __exit__(self, type, value, traceback):
        self.close()
    def ensure_connected(self):
        if self._c is None:
            raise IfcbConnectionError('IFCB is not connected')
    def is_responding(self):
        # tries to get NetBIOS name to see if IFCB is responding
        if self._c is not None:
            return True
        else:
            try:
                get_netbios_name(self.addr, timeout=self.timeout)
                return True
            except:
                return False
    def list_shares(self):
        self.ensure_connected()
        for share in self._c.listShares():
            if share.type == SharedDevice.DISK_TREE:
                yield share.name
    def share_exists(self):
        self.ensure_connected()
        for share in self.list_shares():
            if share.lower() == self.share.lower():
                return True
        return False
    def list_filesets(self):
        """list fileset lids, most recent first"""
        self.ensure_connected()
        fs = defaultdict(lambda: 0)
        for f in self._c.listPath(self.share, ''):
            if f.isDirectory:
                continue
            fn = f.filename
            lid, ext = os.path.splitext(fn)
            if ext in ['.hdr','.roi','.adc']:
                fs[lid] += 1
        complete_sets = []
        for lid, c in fs.items():
            if c == 3: # complete fileset
                complete_sets.append(lid)
        return sorted(complete_sets, reverse=True)
    def transfer_fileset(self, lid, local_directory, skip_existing=True):
        self.ensure_connected()
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
                self._c.retrieveFile(self.share, remote_path, fout, timeout=self.timeout)
            os.rename(temp_local_path, local_path)
    def sync(self, local_directory, progress_callback=do_nothing):
        # local_directory can be
        # * a path, or
        # * a callbale returning a path when passed a bin lid
        self.ensure_connected()
        fss = self.list_filesets()
        copied = []
        failed = []
        for lid in fss:
            try:
                if callable(local_directory):
                    destination_directory = local_directory(lid)
                self.transfer_fileset(lid, destination_directory, skip_existing=True)
                copied.append(lid)
            except:
                failed.append(lid)
            progress_callback({
                'total': len(fss),
                'copied': copied,
                'failed': failed,
                'lid': lid
                })
