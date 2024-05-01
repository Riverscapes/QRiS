
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDate

from qgis.core import QgsProject, QgsVectorLayer
from qgis.utils import iface
from qgis.gui import QgsMapToolEmitPoint, QgsMapToolIdentifyFeature

from ..lib.climate_engine import get_datasets, get_dataset_variables, get_dataset_date_range, get_dataset_timeseries_polygon


class FrmClimateEngine(QtWidgets.QDialog):

    def __init__(self, parent: QtWidgets.QWidget = None):

        self.iface = iface
        self.layer_geometry = None

        super().__init__(parent)

        self.setWindowTitle('Climate Engine')
        self.setupUi()

        self.datasets = get_datasets()
        self.cboDataset.addItems(self.datasets.keys())

        # get the layer geometry from the selected feature of the active layer
        active_layer = iface.activeLayer()
        if active_layer is not None:
            self.layer_geometry = active_layer.selectedFeatures()[0].geometry()
            self.txtGeometry.setText(self.layer_geometry.asWkt())

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
        # self.btnSelectGeometry.setEnabled(True)
        self.btnGetTimeseries.setEnabled(True)

    def select_geometry(self):

        self.mapTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.mapTool.canvasClicked.connect(self.on_canvas_clicked)
        self.iface.mapCanvas().setMapTool(self.mapTool)

    def on_canvas_clicked(self, point, button):
            
            self.iface.mapCanvas().unsetMapTool(self.mapTool)
    
            layer = iface.activeLayer()
            self.identifyTool = QgsMapToolIdentifyFeature(self.iface.mapCanvas(), layer)
            self.identifyTool.featureIdentified.connect(self.on_feature_identified)
            self.identifyTool.setLayer(layer)
            self.iface.mapCanvas().setMapTool(self.identifyTool)

    def on_feature_identified(self, feature):
            
            self.iface.mapCanvas().unsetMapTool(self.identifyTool)
            self.txtGeometry.setText(feature.geometry().asWkt())
            self.btnSelectGeometry.setEnabled(False)

    def retrieve_timeseries(self):

        if self.layer_geometry is None:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select a geometry')
            return
        
        if self.lboxVariables.count() == 0:
            return
        
        variables = []
        for i in range(self.lboxVariables.count()):
            item = self.lboxVariables.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                variables.append(item.text())
        
        if len(variables) == 0:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Select at least one variable')
            return

        dataset = self.datasets.get(self.cboDataset.currentText())['id']

        start_date = self.dateStartDate.date().toString('yyyy-MM-dd')
        end_date = self.dateEndDate.date().toString('yyyy-MM-dd')

        result = get_dataset_timeseries_polygon(dataset, variables[0], start_date, end_date, self.layer_geometry)        

        if result is not None:
            self.lblStatus.setText('Timeseries retrieved successfully')
            QtWidgets.QMessageBox.information(self, 'Timeseries', f'{result}')
        else:
            self.lblStatus.setText('Error retrieving timeseries')

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
        self.btnSelectGeometry.clicked.connect(self.select_geometry)
        self.horizGeometry.addWidget(self.btnSelectGeometry)
        self.btnSelectGeometry.setEnabled(False)

        self.horizTimeseries = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horizTimeseries)

        self.horizTimeseries.addStretch()

        self.btnGetTimeseries = QtWidgets.QPushButton('Get Timeseries')
        self.btnGetTimeseries.clicked.connect(self.retrieve_timeseries)
        self.horizTimeseries.addWidget(self.btnGetTimeseries)
        self.btnGetTimeseries.setEnabled(False)

        self.lblStatus = QtWidgets.QLabel()
        self.vert.addWidget(self.lblStatus)
        
        self.cboDataset.currentIndexChanged.connect(self.on_dataset_changed)





