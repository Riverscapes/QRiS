from PyQt5 import QtCore, QtGui, QtWidgets
from ..model.db_item import DBItem, DBItemModel


class FrmLayerPicker(QtWidgets.QDialog):

    def __init__(self, parent, label_message: str, layers: list):
        super().__init__(parent)
        self.setupUi()

        self.layer = None

        self.lblMessage.setText(label_message)

        self.model = DBItemModel({i: layers[i] for i in range(len(layers))})
        self.cboLayers.setModel(self.model)

        # Prevent clicking OK if there are no layers
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(len(layers) > 0)

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
        super(FrmLayerPicker, self).accept()
