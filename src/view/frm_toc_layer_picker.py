from PyQt5 import QtCore, QtGui, QtWidgets

from qgis.core import QgsVectorLayer
from qgis.utils import iface


class FrmTOCLayerPicker(QtWidgets.QDialog):

    def __init__(self, parent, label_message: str, layer_types: list = None):
        super().__init__(parent)
        self.setWindowTitle("Select layer")
        self.setupUi()

        self.layer = None

        self.lblMessage.setText(label_message)
        self.model = QtGui.QStandardItemModel()

        for layer in iface.mapCanvas().layers():
            if layer_types is not None:
                if isinstance(layer, QgsVectorLayer):
                    if layer.geometryType() in layer_types:
                        if layer.isTemporary():
                            item = QtGui.QStandardItem(layer.name())
                            item.setData(layer, QtCore.Qt.UserRole)
                            self.model.appendRow(item)

        self.layer_count = self.model.rowCount()
        if self.layer_count > 0:
            self.cboLayers.setModel(self.model)
        else:
            # No layers of the specified type found show messagebox and close this form
            QtWidgets.QMessageBox.warning(self, "No Temporary Layers found", "No temporary layers of the specified geometry type found in the map Table of Contents. \n\nMake sure you have at least one temporary in the Table of Contents and that it is turned on (checked).")

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
