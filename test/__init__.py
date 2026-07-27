"""Test package bootstrap helpers.

This module keeps older test import styles working under package-based
discovery, where tests are imported as ``qris_dev.test.<module>``.
"""

import importlib
import sys

# Backward compatibility for tests that still do `from utilities import ...`.
from . import utilities as _test_utilities

sys.modules.setdefault("utilities", _test_utilities)


# Backward compatibility for tests that still do `from src...`.
try:
    _src_pkg = importlib.import_module("qris_dev.src")
    sys.modules.setdefault("src", _src_pkg)
except Exception:
    # If import fails here, the failing tests will surface the concrete reason.
    pass
