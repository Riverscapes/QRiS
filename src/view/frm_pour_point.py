from PyQt5 import QtCore, QtGui, QtWidgets
from ..model.pour_point import PourPoint
from ..model.project import Project
from ..model.basin_characteristics_table_view import BasinCharsTableModel
from .utilities import validate_name, add_standard_form_buttons


class FrmPourPoint(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, latitude: float, longitude: float, pour_point: PourPoint):
        super().__init__(parent)
        self.setupUi()

        self.pour_point = pour_point
        self.project = project

        if self.pour_point is None:
            self.setWindowTitle('Create New Pour Point with Catchment')

            self.txtLatitude.setText(str(latitude))
            self.txtLongitude.setText(str(longitude))

            self.tabWidget.removeTab(1)
            self.tabWidget.removeTab(1)
        else:
            self.setWindowTitle('Pour Point Details')

            self.chkDelineate.setVisible(False)
            self.chkBasin.setVisible(False)
            self.chkFlowStats.setVisible(False)

            self.txtName.setText(pour_point.name)
            self.txtDescription.setPlainText(pour_point.description)

            self.txtLatitude.setText(str(pour_point.latitude))
            self.txtLongitude.setText(str(pour_point.longitude))

            # Load the basin characteristics
            if pour_point.basin_chars is not None and 'parameters' in pour_point.basin_chars:
                basin_data = [(param['name'], param['code'], param['unit'], param['value']) for param in pour_point.basin_chars['parameters']]
                self.basin_model = BasinCharsTableModel(basin_data, ['Name', 'Code', 'Units', 'Value'])
                self.basinTable.setModel(self.basin_model)

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if self.pour_point is not None:
            try:
                self.pour_point.update(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A pour point with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Pour Point', str(ex))
                return

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

        # self.tabBasin = QtWidgets.QTableWidget()
        self.basinTable = QtWidgets.QTableView()
        self.basinTable.verticalHeader().hide()
        self.tabWidget.addTab(self.basinTable, 'Basin Characteristics')

        self.tabFlow = QtWidgets.QTableWidget()
        self.tabWidget.addTab(self.tabFlow, 'Flow Statistics')

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(True)
        self.vert.addWidget(self.chkAddToMap)

        self.vert.addLayout(add_standard_form_buttons(self, 'pour_point'))


if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    window = FrmPourPoint(None, 123, 123)
    window.show()
    app.exec_()
