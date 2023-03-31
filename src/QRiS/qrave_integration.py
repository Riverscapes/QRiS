import os
import importlib

from qgis.PyQt.QtCore import Qt, QObject, pyqtSignal
from qgis.utils import plugins
from qgis.PyQt.QtGui import QStandardItem, QIcon

from .path_utilities import parse_posix_path

# Try to load these plugin names in priority order
NAMES = ['qrave_toolbar_dev', 'qrave_toolbar', 'QRAVEPlugin-qrave_integration']


class QRaveIntegration(QObject):

    qrave_to_qris = pyqtSignal(str, str)

    def __init__(self, parent):
        super(QRaveIntegration, self).__init__(parent)
        # from https://gis.stackexchange.com/questions/403501/using-qgis-plugin-from-another-plugin
        self.name = next((pname for pname in NAMES if pname in plugins), None)
        self.plugin_instance = plugins[self.name] if self.name is not None else None
        self.qrave_map_layer = None

        # This is how we pull uninstantiated code from QRave. We need to load it as a module
        if self.name:
            self.qrave_map_layer = importlib.import_module(f'{self.name}.src.classes.qrave_map_layer')
            self.symbology_folder = parse_posix_path(os.path.join(self.qrave_map_layer.SYMBOLOGY_DIR, 'QRiS'))

        if self.plugin_instance and self.plugin_instance.dockwidget:
            # Check if the signal is already connected
            if self.plugin_instance.dockwidget.receivers(self.plugin_instance.dockwidget.layerMenuOpen) > 0:
                self.plugin_instance.dockwidget.layerMenuOpen.disconnect()
            self.plugin_instance.dockwidget.layerMenuOpen.connect(self.qrave_add_to_map_menu_item)

    def qrave_add_to_map_menu_item(self, menu, item: QStandardItem, data):
        """Custom menu to show at the bottom of the QRave context menu

        Args:
            menu (_type_): ContextMenu(QMenu) object from QRave
            item (QStandardItem): QStandardItem (PyQt)
            data (ProjectTreeData): ProjectTreeData (QRave)
        """

        menu.addSeparator()
        menu.addCustomAction(QIcon(f':/plugins/qris_toolbar/add_to_map'), "Add to QRiS", lambda: self.add_to_qris(item, data))

    def add_to_qris(self, item, data):
        """_summary_

        Args:
            item (QStandardItem): QStandardItem (PyQt)
            data (ProjectTreeData): ProjectTreeData (QRave)
        """

        layer = item.data(Qt.UserRole).data
        if layer.layer_type == 'raster':
            path = layer.layer_uri
        else:
            path = f'{layer.layer_uri}|layername={layer.layer_name}'
        self.qrave_to_qris.emit(path, layer.layer_type)
