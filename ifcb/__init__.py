"""IFCB data API"""

import pkgutil

__path__ = pkgutil.extend_path(__path__, __name__)

# high-level API

from .data.adc import SCHEMA_VERSION_1, SCHEMA_VERSION_2
from .data.files import DataDirectory
from .data.identifiers import Pid

# I/O helper functions

from .data.io import open_raw, open_hdf, open_zip, open_mat
from .data.remote import open_url

# low-level API

from .data.adc import parse_adc_file
from .data.hdr import parse_hdr_file
from .data.roi import read_image
