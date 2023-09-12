import os
from osgeo import gdal

from PyQt5 import QtCore, QtWidgets
from qgis.core import QgsVectorLayer, QgsGeometry, QgsPolygon

from rsxml.project_xml import Project, MetaData, Meta, ProjectBounds, Coords, BoundingBox, Realization, Geopackage, GeopackageLayer, GeoPackageDatasetTypes

from ...__version__ import __version__ as qris_version
from ..model.event import Event
from ..model.project import Project as QRiSProject
from ..QRiS.path_utilities import parse_posix_path
from .metadata import MetadataWidget
from .utilities import add_standard_form_buttons


class FrmExportDesign(QtWidgets.QDialog):

    def __init__(self, parent, project: QRiSProject, event: Event):
        super().__init__(parent)

        self.qris_project = project
        self.qris_event = event

        self.setWindowTitle("Export Riverscapes LTPBR Design")
        self.setupUi()

    def accept(self) -> None:

        # check if output path already exists. If so, prompt user to overwrite or cancel
        if os.path.exists(self.txt_outpath.text()):
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("The output path already exists. Do you want to overwrite it?")
            msg.setWindowTitle("Overwrite Output Path?")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
            msg.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            msg.setEscapeButton(QtWidgets.QMessageBox.Cancel)
            ret = msg.exec_()
            if ret == QtWidgets.QMessageBox.Cancel:
                return

        # create a new project folder if it doesn't exist
        if not os.path.exists(self.txt_outpath.text()):
            os.mkdir(self.txt_outpath.text())

        # copy the geopackage layers to the new project folder
        out_geopackage = parse_posix_path(os.path.join(self.txt_outpath.text(), "ltpbr.gpkg"))
        layers = [layer.layer.fc_name for layer in self.qris_event.event_layers]
        gdal.VectorTranslate(out_geopackage,
                             self.qris_project.project_file,
                             format="GPKG",
                             layers=layers)

        # get the project bounds or have user select an aoi?
        envelope = None
        for layer in self.qris_event.event_layers:
            geom = None
            lyr = QgsVectorLayer(f'{self.qris_project.project_file}|layername={layer.layer.fc_name}', layer.layer.name, "ogr")
            lyr.setSubsetString(f"event_id = {layer.event_id}")
            for f in lyr.getFeatures():
                if geom is None:
                    geom = f.geometry()
                else:
                    geom = geom.combine(f.geometry())
            if geom is None:
                continue
            hull = geom.convexHull()
            if envelope is None:
                envelope = hull
            else:
                envelope = envelope.combine(hull)

        extent = envelope.boundingBox()
        centroid = envelope.centroid().asPoint()

        geojson = envelope.asJson()
        # write to file
        geojson_filename = "project_bounds.geojson"
        geojson_path = parse_posix_path(os.path.join(self.txt_outpath.text(), geojson_filename))
        with open(geojson_path, 'w') as f:
            f.write(geojson)

        project_bounds = ProjectBounds(centroid=Coords(centroid.x(), centroid.y()),
                                       bounding_box=BoundingBox(minLat=extent.yMinimum(),
                                                                minLng=extent.xMinimum(),
                                                                maxLat=extent.yMaximum(),
                                                                maxLng=extent.xMaximum()),
                                       filepath=geojson_filename)

        path = parse_posix_path(os.path.join(self.txt_outpath.text(), "project.rs.xml"))
        self.rs_project = Project(name=self.txt_rs_name.text(),
                                  proj_path=path,
                                  project_type='LTPBRDesign',
                                  meta_data=MetaData(values=[Meta('QRiS Project', self.qris_project.name)]),
                                  description=self.txt_description.toPlainText(),
                                  bounds=project_bounds)

        date_created = QtCore.QDateTime.currentDateTime()

        # prepare the datasets
        geopackage_layers = []
        for layer in self.qris_event.event_layers:
            gp_lyr = GeopackageLayer(lyr_name=layer.layer.fc_name,
                                     name=layer.layer.name,
                                     ds_type=GeoPackageDatasetTypes.VECTOR)
            geopackage_layers.append(gp_lyr)

        gpkg = Geopackage(xml_id='ltpbr_gpkg_01',
                          name='ltpbr',
                          path='ltpbr.gpkg',
                          layers=geopackage_layers)

        realization = Realization(xml_id='realization_1',
                                  name=self.qris_event.name,
                                  date_created=date_created.toPyDateTime(),
                                  product_version=qris_version,
                                  datasets=[gpkg])

        # add description if it exists
        if self.qris_event.description:
            realization.description = self.qris_event.description

        self.rs_project.realizations.append(realization)

        # Metadata from project?
        # metadata from design?

        self.rs_project.write()

        return super().accept()

    def browse_path(self):

        basepath = os.path.dirname(self.qris_project.project_file)
        # path = QtWidgets.QFileDialog.getSaveFileName(self, "Export Riverscapes LTPBR Design", basepath, "XML Files (project.rs.xml)")[0]
        path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', basepath, QtWidgets.QFileDialog.ShowDirsOnly)
        if path:
            # check if a project.rs.xml file already exists in the selected folder
            if os.path.exists(path):
                if os.path.exists(os.path.join(path, "project.rs.xml")):
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Warning)
                    msg.setText("A Riverscapes project file already exists in the selected folder. Do you want to overwrite it?")
                    msg.setWindowTitle("Overwrite Project File?")
                    msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
                    msg.setDefaultButton(QtWidgets.QMessageBox.Cancel)
                    msg.setEscapeButton(QtWidgets.QMessageBox.Cancel)
                    ret = msg.exec_()
                    if ret == QtWidgets.QMessageBox.Cancel:
                        return

        self.txt_outpath.setText(path)

    def setupUi(self):

        self.setMinimumSize(500, 300)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        # add grid layout
        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        # add label and txt box for project name
        self.lbl_project = QtWidgets.QLabel("Project Name")
        self.grid.addWidget(self.lbl_project, 0, 0, 1, 1)

        self.txt_rs_name = QtWidgets.QLineEdit()
        self.txt_rs_name.setReadOnly(False)
        self.txt_rs_name.setText(self.qris_project.name)
        self.grid.addWidget(self.txt_rs_name, 0, 1, 1, 1)

        # add label and horizontal layout with textbox and small button for output path
        self.lbl_output = QtWidgets.QLabel("Output Path")
        self.grid.addWidget(self.lbl_output, 1, 0, 1, 1)

        self.horiz_output = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz_output, 1, 1, 1, 1)

        self.txt_outpath = QtWidgets.QLineEdit()
        self.txt_outpath.setReadOnly(True)
        self.horiz_output.addWidget(self.txt_outpath)

        self.btn_output = QtWidgets.QPushButton("...")
        self.btn_output.setMaximumWidth(30)
        self.btn_output.clicked.connect(self.browse_path)
        self.horiz_output.addWidget(self.btn_output)

        # add multiline box for description
        self.lbl_description = QtWidgets.QLabel("Description")
        self.grid.addWidget(self.lbl_description, 2, 0, 1, 1)

        self.txt_description = QtWidgets.QTextEdit()
        self.txt_description.setReadOnly(False)
        self.txt_description.setText(self.qris_event.description)
        self.grid.addWidget(self.txt_description, 2, 1, 1, 1)

        # add vertical spacer
        self.vert.addStretch()

        # add standard form buttons
        self.vert.addLayout(add_standard_form_buttons(self, "export_metrics"))
