from qgis.PyQt.QtWidgets import QDockWidget, QWidget, QTreeView, QVBoxLayout, QMenu, QAction
from qgis.PyQt.QtCore import pyqtSlot, QModelIndex
from qgis.PyQt.QtGui import QIcon, QStandardItem


class ContextMenu(QMenu):
    MENUS = {
        'EXPAND_ALL': (
            "Expand All Child Nodes",
            ':/plugins/ript_toolbar/expand.png',
        ),
        'COLLAPSE_ALL': (
            "Collapse All Child Nodes",
            ':/plugins/ript_toolbar/expand.png',
        ),
        'ADD_ALL_TO_MAP': (
            "Add All Layers To The Map",
            ':/plugins/ript_toolbar/AddToMap.png',
        ),
        'ADD_TO_MAP': (
            "Add to Map",
            ':/plugins/ript_toolbar/AddToMap.png',
        ),
        'BROWSE_PROJECT_FOLDER': (
            'Browse Project Folder',
            ':/plugins/ript_toolbar/BrowseFolder.png'
        ),
        'OPEN_FILE': (
            'Open File',
            ':/plugins/ript_toolbar/RaveAddIn_16px.png'
        ),
        'BROWSE_FOLDER': (
            'Browse Folder',
            ':/plugins/ript_toolbar/BrowseFolder.png'
        ),
        'VIEW_WEB_SOURCE': (
            'View Source Riverscapes Project',
            ':/plugins/ript_toolbar/RaveAddIn_16px.png'
        ),
        'VIEW_LAYER_META': (
            'View Layer MetaData',
            ':/plugins/ript_toolbar/metadata.png'
        ),
        'VIEW_PROJECT_META': (
            'View Project MetaData',
            ':/plugins/ript_toolbar/metadata.png'
        ),
        'REFRESH_PROJECT_HIERARCHY': (
            'Refresh Project Hierarchy',
            ':/plugins/ript_toolbar/refresh.png'
        ),
        'CUSTOMIZE_PROJECT_HIERARCHY': (
            'Customize Project Hierarchy',
            ':/plugins/ript_toolbar/tree.png'
        ),
        'CLOSE_PROJECT': (
            'Close Project',
            ':/plugins/ript_toolbar/close.png'
        ),
        'WAREHOUSE_VIEW': (
            'View in Warehouse',
            ':/plugins/ript_toolbar/RaveAddIn_16px.png'
        ),
        'ADD_DETRENDED_RASTER': (
            'Add Detrended Raster to Project',
            ':/plugins/ript_toolbar/OpenProject.png'),
        'EXPLORE_ELEVATIONS': (
            'Explore Elevations...',
            ':/plugins/ript_toolbar/elevations.svg'
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
