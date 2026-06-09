from qgis.PyQt import QtCore, QtGui, QtWidgets

from qgis.core import QgsRasterLayer, QgsVectorLayer
from qgis.utils import iface


class FrmTOCLayerPicker(QtWidgets.QDialog):

    @staticmethod
    def _is_web_raster_layer(layer: QgsRasterLayer) -> bool:
        provider = (layer.providerType() or '').lower()
        if provider in ['wms', 'xyz', 'arcgismapserver', 'arcgisfeatureserver']:
            return True

        source = ((layer.source() or '') + '|' + (layer.dataProvider().dataSourceUri() or '')).lower()
        return 'type=xyz' in source or 'tilematrixset' in source or 'service=wms' in source

    def __init__(self, parent, label_message: str, layer_types: list = None, temporary_layers_only: bool = True, exclude_datasource_prefix: str = None, exclude_empty_layers: bool = False, include_raster_layers: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Select layer")
        self.setupUi()

        self.layer = None

        self.lblMessage.setText(label_message)
        self.model = QtGui.QStandardItemModel()

        for layer in iface.mapCanvas().layers():
            if isinstance(layer, QgsVectorLayer):
                if layer_types is not None and layer.geometryType() not in layer_types:
                    continue
                if temporary_layers_only and not layer.isTemporary():
                    continue
                if exclude_empty_layers and layer.featureCount() == 0:
                    continue
                if exclude_datasource_prefix is not None:
                    if layer.dataProvider().dataSourceUri().startswith(exclude_datasource_prefix):
                        continue
                item = QtGui.QStandardItem(layer.name())
                item.setData(layer, QtCore.Qt.UserRole)
                self.model.appendRow(item)
                continue

            if include_raster_layers and isinstance(layer, QgsRasterLayer):
                if self._is_web_raster_layer(layer):
                    continue
                if temporary_layers_only and hasattr(layer, 'isTemporary') and not layer.isTemporary():
                    continue
                if exclude_empty_layers and layer.bandCount() == 0:
                    continue
                if exclude_datasource_prefix is not None:
                    if layer.dataProvider().dataSourceUri().startswith(exclude_datasource_prefix):
                        continue
                item = QtGui.QStandardItem(layer.name())
                item.setData(layer, QtCore.Qt.UserRole)
                self.model.appendRow(item)

        self.layer_count = self.model.rowCount()
        if self.layer_count > 0:
            self.cboLayers.setModel(self.model)
        else:
            # No layers of the specified type found show messagebox and close this form
            temporary_text = "temporary " if temporary_layers_only else ""
            
            QtWidgets.QMessageBox.warning(self, f"No {temporary_text}Layers found", f"No {temporary_text}layers of the specified type found in the map Table of Contents. \n\nMake sure you have at least one {temporary_text}layer in the Table of Contents and that it is turned on (checked).")

    def setupUi(self):

        self.resize(400, 100)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblMessage = QtWidgets.QLabel()
        self.grid.addWidget(self.lblMessage, 0, 0, 1, 1)

        self.cboLayers = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboLayers, 0, 1, 1, 1)

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.vert.addWidget(self.buttonBox)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def accept(self):

        self.layer = self.cboLayers.currentData(QtCore.Qt.UserRole)
        super(FrmTOCLayerPicker, self).accept()
