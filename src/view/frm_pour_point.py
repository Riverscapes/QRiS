from PyQt5 import QtCore, QtGui, QtWidgets


class FrmPourPoint(QtWidgets.QDialog):

    def __init__(self, parent, latitude, longitude):
        super().__init__(parent)
        self.setupUi()

        self.setWindowTitle('Create New Pour Point with Catchment')

        self.txtLatitude.setText(str(latitude))
        self.txtLongitude.setText(str(longitude))

    def accept(self):

        if len(self.txtName.text()) < 1:
            QtWidgets.QMessageBox.warning(self, 'Missing Name', 'You must provide a pour point name to continue.')
            self.txtName.setFocus()
            return ()

        super().accept()

    def setupUi(self):
        # self.setObjectName("PoutPoint")
        self.resize(640, 480)

        self.vert = QtWidgets.QVBoxLayout()
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.horiz = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz)

        self.lblLatitude = QtWidgets.QLabel()
        self.lblLatitude.setText('Latitude')
        self.horiz.addWidget(self.lblLatitude)

        self.txtLatitude = QtWidgets.QLineEdit()
        self.txtLatitude.setReadOnly(True)
        self.horiz.addWidget(self.txtLatitude)

        self.lblLongitude = QtWidgets.QLabel()
        self.lblLongitude.setText('Longitude')
        self.horiz.addWidget(self.lblLongitude)

        self.txtLongitude = QtWidgets.QLineEdit()
        self.txtLongitude.setReadOnly(True)
        self.horiz.addWidget(self.txtLongitude)

        self.chkDelineate = QtWidgets.QCheckBox()
        self.chkDelineate.setText('Delineate Watershed Catchment')
        self.chkDelineate.setEnabled(False)
        self.chkDelineate.setChecked(True)
        self.vert.addWidget(self.chkDelineate)

        self.chkBasin = QtWidgets.QCheckBox()
        self.chkBasin.setText('Calculate Basin Characteristics (additional 60 secs)')
        self.vert.addWidget(self.chkBasin)

        self.chkFlowStats = QtWidgets.QCheckBox()
        self.chkFlowStats.setText('Calculate Flow Statistics (additional 60 secs)')
        self.vert.addWidget(self.chkFlowStats)

        self.tabWidget = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabWidget)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tabWidget.addTab(self.txtDescription, 'Description')

        self.tabBasin = QtWidgets.QTableWidget()
        self.tabWidget.addTab(self.tabBasin, 'Basin Characteristics')

        self.tabFlow = QtWidgets.QTableWidget()
        self.tabWidget.addTab(self.tabFlow, 'Flow Statistics')

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.vert.addWidget(self.buttonBox)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    window = FrmPourPoint(None, 123, 123)
    window.show()
    app.exec_()
