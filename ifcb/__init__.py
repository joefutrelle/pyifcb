"""IFCB data API"""

import pkgutil

__path__ = pkgutil.extend_path(__path__, __name__)

from .data.toplevel import *

try:
    from ifcb.db.toplevel import *
except ImportError:
    pass
