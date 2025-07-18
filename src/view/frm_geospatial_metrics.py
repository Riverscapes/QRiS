import os
from PyQt5 import QtCore, QtGui, QtWidgets

from .frm_geospatial_metrics_options import FrmOptions
from .frm_geospatial_metrics_export import FrmGeospatialMetricsExport

from ..model.project import Project
from ..model.sample_frame import SampleFrame

from .utilities import add_standard_form_buttons


class FrmGeospatialMetrics(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, mask: SampleFrame, polygons: dict, metrics: dict):
        super().__init__(parent)

        self.qris_project = project
        self.qris_mask = mask
        self.metrics = metrics
        self.polygons = polygons

        self.setupUi()

        self.setWindowTitle(f'Zonal Statistics for {self.qris_mask.name}')

        self.txtMask.setText(self.qris_mask.name)

        self.load_tree()

    def load_tree(self):

        # The data are organized layer then polygon. Need to invert if necessary
        display_data = self.metrics
        # if self.rdoPolygonsFirst.isChecked() is True:
        #     display_data = None
        #     for layer_name, values in self.metrics:
        #         for polygon_id

        self.treeModel = QtGui.QStandardItemModel()
        self.treeModel.setColumnCount(2)
        self.treeModel.setHorizontalHeaderLabels(['Layer / Polygon / Metric', 'Value'])

        for layer_name, values in display_data.items():
            layer_item = QtGui.QStandardItem(layer_name)
            for polygon_id, poly_values in values.items():
                polygon_label = self.polygons[polygon_id]['display_label']
                poly_item = QtGui.QStandardItem(polygon_label)
                layer_item.appendRow(poly_item)

                for metric_name, metric_value in poly_values.items():
                    metric_item = QtGui.QStandardItem(metric_name)
                    if metric_value is None:
                        metric_value_str = ''
                    elif isinstance(metric_value, float):
                        metric_value_str = '{:,.2f}'.format(metric_value)
                    else:
                        metric_value_str = '{:,}'.format(metric_value)
                    metric_value_item = QtGui.QStandardItem(str(metric_value_str))
                    poly_item.appendRow([metric_item, metric_value_item])

                    # metric_item.appendColumn([metric_value_item])

            self.treeModel.appendRow(layer_item)

        self.tree.setModel(self.treeModel)
        self.tree.expandAll()

    def on_export(self):
        frm = FrmGeospatialMetricsExport(self, self.qris_project, self.qris_mask, self.polygons, self.metrics)
        frm.exec_()

    def on_settings(self):
        # frm = FrmOptions(self, None)
        # frm.exec_()
        QtWidgets.QMessageBox.warning(None, 'Settings', 'This Feature Is Not Implemented.')

    def accept(self):

        super().accept()

    def setupUi(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.txtMask = QtWidgets.QLineEdit()
        self.txtMask.setReadOnly(True)
        self.vert.addWidget(self.txtMask)

        self.horizCommands = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horizCommands)

        self.rdoPolygonsFirst = QtWidgets.QRadioButton('Polygons then Layers')
        self.rdoPolygonsFirst.setEnabled(False)
        self.horizCommands.addWidget(self.rdoPolygonsFirst)

        self.rdoLayersFirst = QtWidgets.QRadioButton('Layers then Polygons')
        self.rdoLayersFirst.setChecked(True)
        self.horizCommands.addWidget(self.rdoLayersFirst)

        self.horizCommands.addStretch()

        self.cmdExport = QtWidgets.QPushButton('Export Data')
        self.cmdExport.clicked.connect(self.on_export)
        self.horizCommands.addWidget(self.cmdExport)

        # self.cmdSettings = QtWidgets.QPushButton('Settings')
        # self.cmdSettings.clicked.connect(self.on_settings)
        # self.horizCommands.addWidget(self.cmdSettings)

        self.tree = QtWidgets.QTreeView()
        self.vert.addWidget(self.tree)

        self.vert.addLayout(add_standard_form_buttons(self, 'zonal-statistics'))
