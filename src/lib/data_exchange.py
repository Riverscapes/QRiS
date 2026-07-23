from qgis.PyQt import QtCore, QtGui

from ..QRiS.settings import CONSTANTS
from .map import get_map_center, get_zoom_level


def browse_data_exchange(canvas):
    """Open the Riverscapes Data Exchange project search in the default browser,
    centred on the current map view."""
    center = get_map_center(canvas)
    zoom = get_zoom_level(canvas)
    search_url = f"{CONSTANTS['warehouseUrl']}/s?type=Project&bounded=1&view=map&geo={center.x()}%2C{center.y()}%2C{zoom}"
    QtGui.QDesktopServices.openUrl(QtCore.QUrl(search_url))
