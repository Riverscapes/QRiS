from qgis.PyQt.QtWidgets import QDockWidget, QWidget, QTreeView, QVBoxLayout, QMenu, QAction
from qgis.PyQt.QtCore import pyqtSlot, QModelIndex
from qgis.PyQt.QtGui import QIcon, QStandardItem


class ContextMenu(QMenu):
    MENUS = {
        'EXPAND_ALL': (
            "Expand All Child Nodes",
            ':/plugins/qris_toolbar/expand.png',
        ),
        'COLLAPSE_ALL': (
            "Collapse All Child Nodes",
            ':/plugins/qris_toolbar/expand.png',
        ),
        'ADD_ALL_TO_MAP': (
            "Add All Layers To The Map",
            ':/plugins/qris_toolbar/AddToMap.png',
        ),
        'ADD_TO_MAP': (
            "Add to Map",
            ':/plugins/qris_toolbar/AddToMap.png',
        ),
        'BROWSE_PROJECT_FOLDER': (
            'Browse Project Folder',
            ':/plugins/qris_toolbar/BrowseFolder.png'
        ),
        'OPEN_FILE': (
            'Open File',
            ':/plugins/qris_toolbar/RaveAddIn_16px.png'
        ),
        'BROWSE_FOLDER': (
            'Browse Folder',
            ':/plugins/qris_toolbar/BrowseFolder.png'
        ),
        'VIEW_WEB_SOURCE': (
            'View Source Riverscapes Project',
            ':/plugins/qris_toolbar/RaveAddIn_16px.png'
        ),
        'VIEW_LAYER_META': (
            'View Layer MetaData',
            ':/plugins/qris_toolbar/metadata.png'
        ),
        'VIEW_PROJECT_META': (
            'View Project MetaData',
            ':/plugins/qris_toolbar/metadata.png'
        ),
        'REFRESH_PROJECT_HIERARCHY': (
            'Refresh Project Hierarchy',
            ':/plugins/qris_toolbar/refresh.png'
        ),
        'CUSTOMIZE_PROJECT_HIERARCHY': (
            'Customize Project Hierarchy',
            ':/plugins/qris_toolbar/tree.png'
        ),
        'CLOSE_PROJECT': (
            'Close Project',
            ':/plugins/qris_toolbar/close.png'
        ),
        'WAREHOUSE_VIEW': (
            'View in Warehouse',
            ':/plugins/qris_toolbar/RaveAddIn_16px.png'
        ),
        'ADD_DETRENDED_RASTER': (
            'Add Detrended Raster to Project',
            ':/plugins/qris_toolbar/OpenProject.png'),
        'ADD_PROJECT_LAYER': (
            'Add layer to the RIPT Project',
            ':/plugins/qris_toolbar/OpenProject.png'
        ),
        'EXPLORE_ELEVATIONS': (
            'Explore Elevations...',
            ':/plugins/qris_toolbar/Detrend.png'
        ),
        'ADD_ASSESSMENT': (
            'New Riverscape Assessment',
            ':/plugins/qris_toolbar/Detrend.png'
        ),
        'ADD_DESIGN': (
            'New Low-Tech Design',
            ':/plugins/qris_toolbar/Detrend.png'
        )
    }

    # def __init__(self):
    #     self.menu = ContextMenu()
    #     super().__init__(self)

    def addAction(self, lookup: str, slot: pyqtSlot = None, enabled=True):
        if lookup not in self.MENUS:
            raise Exception('Menu not found')
        action_text = self.MENUS[lookup]
        action = super().addAction(QIcon(action_text[1]), action_text[0])
        action.setEnabled(enabled)

        if slot is not None:
            action.triggered.connect(slot)
