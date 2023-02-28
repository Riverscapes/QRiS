import os
import importlib

from qgis.PyQt.QtCore import Qt
from qgis.utils import plugins
from qgis.PyQt.QtGui import QStandardItem, QIcon


# Try to load these plugin names in priority order
NAMES = ['qrave_toolbar_dev', 'qrave_toolbar']


class QRaveIntegration():

    def __init__(self):
        # from https://gis.stackexchange.com/questions/403501/using-qgis-plugin-from-another-plugin
        self.name = next((pname for pname in NAMES if pname in plugins), None)
        self.plugin_instance = plugins[self.name] if self.name is not None else None
        self.qrave_map_layer = None

        # This is how we pull uninstantiated code from QRave. We need to load it as a module
        if self.name:
            self.qrave_map_layer = importlib.import_module(f'{self.name}.src.classes.qrave_map_layer')
            self.symbology_folder = os.path.join(self.qrave_map_layer.SYMBOLOGY_DIR, 'QRiS')

        if self.plugin_instance and self.plugin_instance.dockwidget:
            self.plugin_instance.dockwidget.layerMenuOpen.connect(self.qrave_add_to_map_menu_item)

    def qrave_add_to_map_menu_item(self, menu, item: QStandardItem, data):
        """Custom menu to show at the bottom of the QRave context menu

        Args:
            menu (_type_): ContextMenu(QMenu) object from QRave
            item (QStandardItem): QStandardItem (PyQt)
            data (ProjectTreeData): ProjectTreeData (QRave)
        """

        # TODO: We get a new menu item every time we reload this code. Do we need a singleton?
        menu.addSeparator()
        menu.addCustomAction(QIcon(f':/plugins/qris_toolbar/add_to_map'), "Add to QRiS", lambda: self.import_to_qris(item, data))

    def import_to_qris(self, item, data):
        """_summary_

        Args:
            item (QStandardItem): QStandardItem (PyQt)
            data (ProjectTreeData): ProjectTreeData (QRave)
        """
        # find the symbology for this layer
        symbology = self.qrave_map_layer.QRaveMapLayer.find_layer_symbology(item)
        print('DO WORK HERE')
