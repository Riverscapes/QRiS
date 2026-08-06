"""
Optional-dependency helpers.

Provides conditional imports and user-facing dialogs for packages that
may not be installed (matplotlib, xlwt, etc.).  View modules should
import from here instead of importing these packages directly.
"""

from typing import Optional

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QMessageBox, QPushButton, QWidget

from ..compat import MSGBOX_ICON_INFORMATION, MSGBOX_OK, MSGBOX_ROLE_HELP

_HELP_URL = "https://qris.riverscapes.net/software-help/missing_imports"


def _open_help():
    """Open the optional-dependencies documentation page in the default browser."""
    QDesktopServices.openUrl(QUrl(_HELP_URL))


# ── matplotlib ─────────────────────────────────────────────────────────────
# Each component is set to None if the corresponding sub-module could not be
# imported.  Check **MATPLOTLIB_AVAILABLE** before using any of them.

FigureCanvas = None
Figure = None
MaxNLocator = None
mdates = None
plt = None
mpl_patches = None
mpl_font_manager = None
ticker = None
MATPLOTLIB_AVAILABLE = False

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except Exception:  # nosec B110 - optional dependency
    pass

try:
    from matplotlib.figure import Figure
except Exception:  # nosec B110
    pass

try:
    import matplotlib.pyplot as plt
except Exception:  # nosec B110
    pass

try:
    from matplotlib import dates as mdates  # noqa: F401 - re-exported optional import
except Exception:  # nosec B110
    pass

try:
    import matplotlib.ticker as ticker  # noqa: F401 - re-exported optional import
except Exception:  # nosec B110
    pass

try:
    from matplotlib.ticker import MaxNLocator  # noqa: F401 - re-exported optional import
except Exception:  # nosec B110
    pass

try:
    from matplotlib import patches as mpl_patches
except Exception:  # nosec B110
    pass

try:
    from matplotlib import font_manager as mpl_font_manager
except Exception:  # nosec B110
    pass

MATPLOTLIB_AVAILABLE = FigureCanvas is not None and Figure is not None and plt is not None

MATPLOTLIB_PATCHES_AVAILABLE = mpl_patches is not None
MATPLOTLIB_FONTMANAGER_AVAILABLE = mpl_font_manager is not None


def require_matplotlib(parent: Optional[QWidget] = None) -> bool:
    """Show a modal dialog if matplotlib is missing and return ``False``.

    Includes a **Help** button that opens the QRiS documentation page
    with platform-specific install instructions.

    Returns ``True`` when matplotlib is available (no dialog shown).
    """
    if MATPLOTLIB_AVAILABLE:
        return True

    msg = QMessageBox(parent)
    msg.setIcon(MSGBOX_ICON_INFORMATION)
    msg.setWindowTitle("Matplotlib Required")
    msg.setText("This feature requires the Matplotlib plotting library.\n\nPlease install Matplotlib and restart QGIS:\n\n    pip install matplotlib\n\nOr use the OSGeo4W shell (Windows) / system package manager.\n")
    help_btn = QPushButton("Help - Platform-specific Instructions")
    help_btn.clicked.connect(_open_help)
    msg.addButton(help_btn, MSGBOX_ROLE_HELP)
    msg.addButton(MSGBOX_OK)
    msg.exec()
    return False


# ── xlwt ───────────────────────────────────────────────────────────────────

xlwt = None
XLWT_AVAILABLE = False

try:
    pass  # nosec B110 - optional dependency
except Exception:  # nosec B110
    pass
else:
    XLWT_AVAILABLE = True


def require_xlwt(parent: Optional[QWidget] = None) -> bool:
    """Show a modal dialog if xlwt is missing and return ``False``.

    Includes a **Help** button that opens the QRiS documentation page
    with platform-specific install instructions.

    Returns ``True`` when xlwt is available (no dialog shown).
    """
    if XLWT_AVAILABLE:
        return True

    msg = QMessageBox(parent)
    msg.setIcon(MSGBOX_ICON_INFORMATION)
    msg.setWindowTitle("Excel Export Requires xlwt")
    msg.setText("Exporting to the legacy Excel (.xls) format requires the xlwt library.\n\nPlease install xlwt and restart QGIS:\n\n    pip install xlwt\n\nAlternatively, use CSV or JSON export formats which have no extra dependencies.\n")
    help_btn = QPushButton("Help - Platform-specific Instructions")
    help_btn.clicked.connect(_open_help)
    msg.addButton(help_btn, MSGBOX_ROLE_HELP)
    msg.addButton(MSGBOX_OK)
    msg.exec()
    return False
