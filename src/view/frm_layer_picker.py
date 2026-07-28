from qgis.PyQt import QtWidgets

from ..compat import DLGBTN_CANCEL, DLGBTN_OK, HORIZONTAL, USER_ROLE
from ..model.db_item import DBItemModel


class FrmLayerPicker(QtWidgets.QDialog):
    def __init__(self, parent, label_message: str, layers: list):
        super().__init__(parent)
        self.setupUi()

        self.setWindowTitle("Select Layer")

        self.layer = None

        self.lblMessage.setText(label_message)

        self.model = DBItemModel({i: layers[i] for i in range(len(layers))})
        self.cboLayers.setModel(self.model)

        # Prevent clicking OK if there are no layers
        self.buttonBox.button(DLGBTN_OK).setEnabled(len(layers) > 0)

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
        self.buttonBox.setOrientation(HORIZONTAL)
        self.buttonBox.setStandardButtons(DLGBTN_CANCEL | DLGBTN_OK)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def accept(self):

        self.layer = self.cboLayers.currentData(USER_ROLE)
        super().accept()
