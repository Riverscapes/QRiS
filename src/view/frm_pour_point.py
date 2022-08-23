from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtWidgets import QMessageBox, QDialog
from ..model.project import Project
from .ui.pour_point import Ui_PoutPoint


class FrmPourPoint(QDialog):  # , Ui_PoutPoint):

    def __init__(self, parent, latitude, longitude):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle('Create New Pour Point with Catchment')

        # self.txtLatitude.setText(str(latitude))
        # self.txtLongitude.setText(str(longitude))

        # self.txtLatitude.setReadOnly(True)
        # self.txtLongitude.setReadOnly(True)

    def accept(self):

        if len(self.txtName.text()) < 1:
            QtWidgets.QMessageBox.warning(self, 'Missing Name', 'You must provide a pour point name to continue.')
            self.txtName.setFocus()
            return ()

        super().accept()

    def setupUi2(self, frm):
        # self.setObjectName("PoutPoint")
        self.resize(640, 480)

        self.verticalLayout = QtWidgets.QVBoxLayout(frm)

        self.gridla = QtWidgets.QGridLayout(frm)

        self.gridLayout = QtWidgets.QGridLayout()

        self.lblName = QtWidgets.QLabel(self)
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        # self.buttonBox = QtWidgets.QDialogButtonBox(PoutPoint)
        # self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        # self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        # self.buttonBox.setObjectName("buttonBox")
        # self.gridLayout.addWidget(self.buttonBox, 6, 1, 1, 1)
        # self.chkBasinChars = QtWidgets.QCheckBox(PoutPoint)
        # self.chkBasinChars.setObjectName("chkBasinChars")
        # self.gridLayout.addWidget(self.chkBasinChars, 3, 1, 1, 1)
        # self.txtDescription = QtWidgets.QTextEdit(PoutPoint)
        # self.txtDescription.setObjectName("txtDescription")
        # self.gridLayout.addWidget(self.txtDescription, 5, 1, 1, 1)
        # self.lb = QtWidgets.QLabel(PoutPoint)
        # self.lb.setObjectName("lb")
        # self.gridLayout.addWidget(self.lb, 1, 0, 1, 1)
        # self.txtLongitude = QtWidgets.QLineEdit(PoutPoint)
        # self.txtLongitude.setObjectName("txtLongitude")
        # self.gridLayout.addWidget(self.txtLongitude, 2, 1, 1, 1)
        # self.txtLatitude = QtWidgets.QLineEdit(PoutPoint)
        # self.txtLatitude.setObjectName("txtLatitude")
        # self.gridLayout.addWidget(self.txtLatitude, 1, 1, 1, 1)
        # self.Description = QtWidgets.QLabel(PoutPoint)
        # self.Description.setObjectName("Description")
        # self.gridLayout.addWidget(self.Description, 5, 0, 1, 1)
        # self.label_3 = QtWidgets.QLabel(PoutPoint)
        # self.label_3.setObjectName("label_3")
        # self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        # self.txtName = QtWidgets.QLineEdit(PoutPoint)
        # self.txtName.setObjectName("txtName")
        # self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        # self.chkFlowStats = QtWidgets.QCheckBox(PoutPoint)
        # self.chkFlowStats.setObjectName("chkFlowStats")
        # self.gridLayout.addWidget(self.chkFlowStats, 4, 1, 1, 1)
        # self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
