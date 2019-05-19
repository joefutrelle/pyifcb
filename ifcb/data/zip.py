from zipfile import ZipFile, ZIP_STORED
import json
from io import StringIO, BytesIO

from functools import lru_cache
import pandas as pd

from .identifiers import Pid
from .adc import SCHEMA, schema_names
from io import BytesIO

from .utils import BaseDictlike
from .bins import BaseBin

from .imageio import format_image, read_image

METADATA_ARCNAME = 'metadata.json'
HEADERS_ARCNAME_SUFFIX = '_headers.json'
ADC_ARCNAME_SUFFIX = '.csv'

def bin2zip_stream(b):
    zip_stream = BytesIO()
    with ZipFile(zip_stream, 'w', compression=ZIP_STORED) as zip:
        # bin metadata as JSON
        metadata = {
            'lid': b.lid,
            'schema': b.pid.schema_version,
            'timestamp': b.timestamp.isoformat()
        }
        zip.writestr(METADATA_ARCNAME, json.dumps(metadata))
        # headers as JSON
        headers_json = json.dumps(b.headers)
        zip.writestr(b.lid + HEADERS_ARCNAME_SUFFIX, headers_json)
        # ADC as CSV
        buf = StringIO()
        # FIXME what float format to use?
        b.adc.to_csv(buf, header=False, index=False)
        zip.writestr(b.lid + ADC_ARCNAME_SUFFIX, buf.getvalue())
        # images as PNGs
        with b:
            for target in b.images:
                image_lid = b.pid.with_target(target, namespace=False)
                arcname = image_lid + '.png'
                buf = format_image(b.images[target], mimetype='image/png')
                zip.writestr(arcname, buf.getvalue())
    zip_stream.seek(0)
    return zip_stream

def bin2zip(b, zip_path):
    zip_bytes = bin2zip_stream(b).getvalue()
    with open(zip_path,'wb') as zout:
        zout.write(zip_bytes)

class ZipImages(BaseDictlike):
    def __init__(self, open_zip_file):
        self._zip = open_zip_file
    def __getitem__(self, arcname):
        # must use temp buffer because PIL seeks to 0
        buf = BytesIO(self._zip.read(arcname))
        return read_image(buf)
    def keys(self):
        return self._zip.namelist()
    def has_key(self, arcname):
        return arcname in self._zip.namelist()

class _ZipBinImages(BaseDictlike):
    def __init__(self, zip_bin):
        self.b = zip_bin
        self.zi = ZipImages(zip_bin._zip)
        s = self.b.schema
        csv = self.b.adc
        csv = csv[csv[s.ROI_WIDTH] != 0]
        self.index = csv.index
    def arcname(self, target):
        return self.b.pid.with_target(target) + '.png'
    def __getitem__(self, target):
        return self.zi[self.arcname(target)]
    def keys(self):
        return self.index
    def has_key(self, k):
        return k in self.index
    
class ZipBin(BaseBin):
    def __init__(self, zip_path):
        self.zip_path = zip_path
        self._zip = None
        self._open()
        self._parse_metadata()
        self.images = _ZipBinImages(self)
    def isopen(self):
        return self._zip is not None
    def _open(self):
        if self.isopen():
            raise ValueError('zip file already open')
        self._zip = ZipFile(self.zip_path, 'r')
    def close(self):
        if not self.isopen():
            raise ValueError('zip file not open')
        self._zip.close()
        self._zip = None
    def __enter__(self):
        return self
    def __exit__(self, *args):
        if self.isopen():
            self.close()
    def _parse_metadata(self):
        j = self._zip.read(METADATA_ARCNAME)
        md = json.loads(j.decode('utf8'))
        self._pid = Pid(md['lid'])
    @property
    def pid(self):
        return self._pid
    @property
    @lru_cache()
    def adc(self):
        arcname = self.lid + ADC_ARCNAME_SUFFIX
        fin = self._zip.open(arcname)
        adc = pd.read_csv(fin, header=None, index_col=False)
        adc.columns = [c for c in adc.columns]
        adc.index = pd.RangeIndex(1, len(adc) + 1)
        return adc
    @property
    @lru_cache()
    def headers(self):
        arcname = self.lid + HEADERS_ARCNAME_SUFFIX
        j = self._zip.read(arcname)
        return json.loads(j.decode('utf8'))
