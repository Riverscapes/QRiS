
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDate

from ..lib.climate_engine import get_datasets, get_dataset_variables, get_dataset_date_range


class FrmClimateEngine(QtWidgets.QDialog):

    def __init__(self, parent: QtWidgets.QWidget = None):

        super().__init__(parent)

        self.setWindowTitle('Climate Engine')
        self.setupUi()

        self.datasets = get_datasets()
        self.cboDataset.addItems(self.datasets.keys())


    def on_dataset_changed(self, index):

        self.lboxVariables.clear()
        self.lboxVariables.setEnabled(False)

        dataset = self.cboDataset.currentText()

        dataset_id = self.datasets.get(dataset)['id']
        variables = get_dataset_variables(dataset_id)

        if variables is not None:
            for variable in variables:
                item = QtWidgets.QListWidgetItem(variable)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                self.lboxVariables.addItem(item)
            self.lboxVariables.setEnabled(True)
        

        date_range = get_dataset_date_range(dataset_id)

        if date_range is not None:
            self.min_date = QDate().fromString(date_range.get('min', ""), 'yyyy-MM-dd')
            self.max_date = QDate().fromString(date_range.get('max', ""), 'yyyy-MM-dd')
            self.dateStartDate.setMinimumDate(self.min_date)
            self.dateEndDate.setMinimumDate(self.min_date)
            self.dateStartDate.setMaximumDate(self.max_date)
            self.dateEndDate.setMaximumDate(self.max_date)
            self.dateStartDate.setDate(self.min_date)
            self.dateEndDate.setDate(self.max_date)
            self.dateStartDate.setEnabled(True)
            self.dateEndDate.setEnabled(True)
        else:
            self.dateStartDate.setDate(QDate())
            self.dateEndDate.setDate(QDate())
            self.dateStartDate.setEnabled(False)
            self.dateEndDate.setEnabled(False)

        self.txtGeometry.setEnabled(True)
        self.btnSelectGeometry.setEnabled(True)
        self.btnGetTimeseries.setEnabled(True)

    def select_geometry(self):

        pass

    def retrieve_timeseries(self):

        pass


    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblDataset = QtWidgets.QLabel('Dataset')
        self.grid.addWidget(self.lblDataset, 1, 0)

        self.cboDataset = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboDataset, 1, 1)

        self.lblVariable = QtWidgets.QLabel('Variables')
        self.grid.addWidget(self.lblVariable, 2, 0)

        self.lboxVariables = QtWidgets.QListWidget()
        self.grid.addWidget(self.lboxVariables, 2, 1)

        self.lblStartDate = QtWidgets.QLabel('Start Date')
        self.grid.addWidget(self.lblStartDate, 3, 0)

        self.lblEndDate = QtWidgets.QLabel('End Date')
        self.grid.addWidget(self.lblEndDate, 4, 0)

        self.dateStartDate = QtWidgets.QDateEdit()
        self.grid.addWidget(self.dateStartDate, 3, 1)
        self.dateStartDate.setEnabled(False)

        self.dateEndDate = QtWidgets.QDateEdit()
        self.grid.addWidget(self.dateEndDate, 4, 1)
        self.dateEndDate.setEnabled(False)

        self.lblGeometry = QtWidgets.QLabel('Geometry')
        self.grid.addWidget(self.lblGeometry, 5, 0)

        self.horizGeometry = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizGeometry, 5, 1)

        self.txtGeometry = QtWidgets.QLineEdit()
        self.horizGeometry.addWidget(self.txtGeometry)
        self.txtGeometry.setEnabled(False)

        self.btnSelectGeometry = QtWidgets.QPushButton('Select Geometry')
        self.horizGeometry.addWidget(self.btnSelectGeometry)
        self.btnSelectGeometry.setEnabled(False)

        self.horizTimeseries = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horizTimeseries)

        self.horizTimeseries.addStretch()

        self.btnGetTimeseries = QtWidgets.QPushButton('Get Timeseries')
        self.horizTimeseries.addWidget(self.btnGetTimeseries)
        self.btnGetTimeseries.setEnabled(False)

        self.lblStatus = QtWidgets.QLabel()
        self.vert.addWidget(self.lblStatus)
        
        self.cboDataset.currentIndexChanged.connect(self.on_dataset_changed)





