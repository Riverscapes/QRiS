import os
import re
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from qgis.core import Qgis, QgsApplication

from ..model.scratch_vector import ScratchVector, insert_scratch_vector, scratch_gpkg_path, get_unique_scratch_fc_name
from ..model.db_item import DBItemModel
from ..model.project import Project

from .utilities import validate_name_unique, validate_name, add_standard_form_buttons

from ..gp.vectorize_task import VectorizeTask


class FrmSliderScratchVector(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, raster_path, threshold_value, inverse: bool = False) -> None:
        super().__init__(parent)
        self.setupUi()

        self.project = project
        self.raster_path = raster_path
        self.threshold_value = threshold_value
        self.scratch_vector = None
        self.inverse = inverse

        self.setWindowTitle('Export Polygon to Scratch Vector')

        self.vector_types_model = DBItemModel(project.lookup_tables['lkp_scratch_vector_types'])
        self.cboVectorType.setModel(self.vector_types_model)

        self.txtName.textChanged.connect(self.on_name_changed)

        self.dbsSimplifyTolerance.setDecimals(5)
        self.dbsSimplifyTolerance.setRange(0.00008, 0.0001)
        self.dbsSimplifyTolerance.setSingleStep(0.00001)
        self.dbsSimplifyTolerance.setValue(0.0001)

        self.dbsSmoothingOffset.setRange(0.25, 0.75)
        self.dbsSmoothingOffset.setSingleStep(0.05)
        self.dbsSmoothingOffset.setValue(0.5)

        self.dbsMinPolygonSize.setDecimals(1)
        self.dbsMinPolygonSize.setMinimum(0.0)
        self.dbsMinPolygonSize.setValue(9.0)

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if validate_name_unique(self.project.project_file, 'scratch_vectors', 'name', self.txtName.text()) is False:
            QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A scratch vector with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
            self.txtName.setFocus()
            return

        try:
            self.fc_name = get_unique_scratch_fc_name(self.project.project_file, self.txtName.text())

            simplify_value = self.dbsSimplifyTolerance.value()
            smoothing_value = self.dbsSmoothingOffset.value()
            min_area_value = self.dbsMinPolygonSize.value()
            gpkg = os.path.dirname(self.txtProjectPath.text())

            vectorize_task = VectorizeTask(self.raster_path, gpkg, self.fc_name, self.threshold_value, simplify_value, smoothing_value, min_area_value, self.inverse)
            vectorize_task.on_complete.connect(self.on_complete)

            self.buttonBox.setEnabled(False)
            QgsApplication.taskManager().addTask(vectorize_task)

        except Exception as ex:
            self.buttonBox.setEnabled(True)
            self.scratch_vector = None
            QtWidgets.QMessageBox.warning(self, 'Error Vectorizing Raster', str(ex))
            return

    @pyqtSlot(bool)
    def on_complete(self, result: bool):

        if result is True:
            # self.iface.messageBar().pushMessage('Feature Class Copy Complete.', 'self.txt.', level=Qgis.Info, duration=5)
            try:
                gpkg = os.path.dirname(self.txtProjectPath.text())

                self.scratch_vector = insert_scratch_vector(
                    self.project.project_file,
                    self.txtName.text(),
                    self.fc_name,
                    gpkg,
                    self.cboVectorType.currentData(QtCore.Qt.UserRole).id,
                    self.txtDescription.toPlainText())
                self.project.scratch_vectors[self.scratch_vector.id] = self.scratch_vector

            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A scratch vector with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Vector', str(ex))
                return

            super(FrmSliderScratchVector, self).accept()
        else:
            # self.iface.messageBar().pushMessage('Vectorize Error', 'Review the QGIS log.', level=Qgis.Critical, duration=5)
            self.buttonBox.setEnabled(True)

    def on_name_changed(self, new_name):

        clean_name = re.sub('[^A-Za-z0-9]+', '', self.txtName.text())
        if len(clean_name) > 0:
            self.txtProjectPath.setText(os.path.join(scratch_gpkg_path(self.project.project_file), clean_name))
        else:
            self.txtProjectPath.setText('')

    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblProjectPath = QtWidgets.QLabel()
        self.lblProjectPath.setText('Project Path')
        self.grid.addWidget(self.lblProjectPath, 1, 0, 1, 1)

        self.txtProjectPath = QtWidgets.QLineEdit()
        self.txtProjectPath.setReadOnly(True)
        self.grid.addWidget(self.txtProjectPath, 1, 1, 1, 1)

        self.lblVectorType = QtWidgets.QLabel()
        self.lblVectorType.setText('Vector Type')
        self.grid.addWidget(self.lblVectorType, 2, 0, 1, 1)

        self.cboVectorType = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboVectorType, 2, 1, 1, 1)

        self.lblSimplifyTolerance = QtWidgets.QLabel()
        self.lblSimplifyTolerance.setText('Simplify Tolerance')
        self.grid.addWidget(self.lblSimplifyTolerance, 3, 0, 1, 1)

        self.dbsSimplifyTolerance = QtWidgets.QDoubleSpinBox()
        self.grid.addWidget(self.dbsSimplifyTolerance, 3, 1, 1, 1)

        self.lblSmoothingOffset = QtWidgets.QLabel()
        self.lblSmoothingOffset.setText('Smooting Offset')
        self.grid.addWidget(self.lblSmoothingOffset, 4, 0, 1, 1)

        self.dbsSmoothingOffset = QtWidgets.QDoubleSpinBox()
        self.grid.addWidget(self.dbsSmoothingOffset, 4, 1, 1, 1)

        self.lblMinPolygonSize = QtWidgets.QLabel()
        self.lblMinPolygonSize.setText('Minimum Polygon Area')
        self.grid.addWidget(self.lblMinPolygonSize, 5, 0, 1, 1)

        self.dbsMinPolygonSize = QtWidgets.QDoubleSpinBox()
        self.grid.addWidget(self.dbsMinPolygonSize, 5, 1, 1, 1)

        # self.lblMask = QtWidgets.QLabel()
        # self.lblMask.setText('Clip to Mask')
        # self.grid.addWidget(self.lblMask, 4, 0, 1, 1)

        # self.cboMask = QtWidgets.QComboBox()
        # self.grid.addWidget(self.cboMask, 4, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel()
        self.lblDescription.setText('Description')
        self.grid.addWidget(self.lblDescription, 6, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription, 6, 1, 1, 1)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setText('Add to Map')
        self.chkAddToMap.setChecked(True)
        self.grid.addWidget(self.chkAddToMap, 7, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'raster_slider'))
