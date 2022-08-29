# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QRiSDockWidget
                                 A QGIS plugin
 QGIS Riverscapes Studio (QRiS)
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-05-06
        git sha              : $Format:%H$
        copyright            : (C) 2021 by North Arrow Research
        email                : info@northarrowresearch.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets
from qgis import core, gui, utils

from .frm_analysis_properties import FrmAnalysisProperties

# from qgis.core import QgsMapLayer
# from qgis.gui import QgsDataSourceSelectDialog
# from qgis.utils import iface

from ..model.project import Project
from ..model.mask import MASK_MACHINE_CODE
from ..model.analysis import ANALYSIS_MACHINE_CODE, Analysis
from ..model.analysis_metric import AnalysisMetric
from ..model.db_item import DB_MODE_CREATE, DB_MODE_IMPORT, DBItem, DBItemModel
from ..model.event import EVENT_MACHINE_CODE, Event
from ..model.basemap import BASEMAP_MACHINE_CODE, Raster
from ..model.mask import MASK_MACHINE_CODE, Mask
from ..model.metric_value import MetricValue, load_metric_values

from .frm_metric_value import FrmMetricValue


class FrmAnalysisDocWidget(QtWidgets.QDockWidget):

    def __init__(self, parent=None):

        super(FrmAnalysisDocWidget, self).__init__(parent)
        self.setupUi()

    def configure_analysis(self, project: Project, analysis: Analysis, event: Event):

        self.project = project
        self.analyis = analysis
        self.txtName.setText(analysis.name)

        with sqlite3.connect(project.project_file) as conn:
            curs = conn.cursor()
            curs.execute('SELECT DISTINCT fid, display_label FROM mask_features WHERE mask_id = ?', [analysis.mask.id])
            segments = {row[0]: DBItem('None', row[0], row[1]) for row in curs.fetchall()}
            self.segments_model = DBItemModel(segments)
            self.cboSegment.setModel(self.segments_model)

        # Events
        self.events_model = DBItemModel(project.events)
        self.cboEvent.setModel(self.events_model)

        # Build the metric table (this will also load the metric values)
        self.build_table()

    def cmdProperties_clicked(self):

        frm = FrmAnalysisProperties(self, self, self.project, self.analyis)
        result = frm.exec_()
        if result is not None and result != 0:
            self.txtName.setText(self.analyis.name)

    def build_table(self):

        self.table.setRowCount(0)
        analysis_metrics = list(self.analyis.analysis_metrics.values())
        self.table.setRowCount(len(analysis_metrics))
        for row in range(len(analysis_metrics)):
            metric = analysis_metrics[row]
            label_metric = QtWidgets.QTableWidgetItem()
            label_metric.setText(metric.metric.name)
            self.table.setItem(row, 0, label_metric)
            label_metric.setData(QtCore.Qt.UserRole, metric)
            label_metric.setFlags(QtCore.Qt.ItemIsEnabled)

        self.table.doubleClicked.connect(self.edit_metric_value)
        # ui.tableWidget, signal(cellDoubleClicked(int,int)), this, SLOT(tableItemClicked(int,int)));

        self.load_table_values()

        self.table.setHorizontalHeaderLabels(['Metric', 'Value', 'Uncertainty'])
        self.table.setColumnWidth(0, self.table.width() * 0.8)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(1, 100)

    def load_table_values(self):

        event = self.cboEvent.currentData(QtCore.Qt.UserRole)
        mask_feature_id = self.cboSegment.currentData(QtCore.Qt.UserRole).id

        if event is not None and mask_feature_id is not None:
            # Load latest metric values from DB
            metric_values = load_metric_values(self.project.project_file, self.analyis, event, mask_feature_id, self.metrics)

            # Loop over active metrics and load values into grid
            for row in range(self.table.rowCount()):
                metric = self.table.cellWidget(row, 0).DATA
                metric_value_text = ''
                uncertainty_text = ''
                if metric.id in metric_values:
                    metric_value = metric_values[metric.id]
                    metric_value_text = metric_value.manual_value if metric_value.is_manual else metric_value.automated_value
                    uncertainty_text = metric_value.uncertainty
                    # TODO: cell formatting
                self.table.cellWidget(row, 1).setText(metric_value_text)
                self.table.cellWidget(row, 2).setText(uncertainty_text)

    def cmdCalculate_clicked(self, row, col):

        QtWidgets.QMessageBox.information(self, 'Not Implemented', 'Calculation of metrics from event layers is not yet implemented.')

    def cmdProperties_clicked(self):

        frm = FrmAnalysisProperties(self, self.project, self.analyis)
        result = frm.exec_()
        if result is not None and result != 0:
            self.txtName.setText(frm.analysis.name)
            self.build_table()

    def edit_metric_value(self, mi):

        metric_value = self.table.item(mi.row(), 0).data(QtCore.Qt.UserRole)
        frm = FrmMetricValue(self, self.project, self.project.metrics, metric_value)
        result = frm.exec_()
        if result is not None and result != 0:
            QtWidgets.QMessageBox.information('Not Implemented', 'TODO: refresh grid')

    def setupUi(self):

        self.setWindowTitle('QRiS Analysis')
        self.dockWidgetContents = QtWidgets.QWidget()

        self.vert = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        # self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Analysis')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.horizName = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizName, 0, 1, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.txtName.setReadOnly(True)
        self.horizName.addWidget(self.txtName)

        self.cmdProperties = QtWidgets.QPushButton()
        self.cmdProperties.setText('Properties')
        self.cmdProperties.clicked.connect(self.cmdProperties_clicked)
        self.horizName.addWidget(self.cmdProperties)

        self.lblEvent = QtWidgets.QLabel()
        self.lblEvent.setText('Data Capture Event')
        self.grid.addWidget(self.lblEvent, 1, 0, 1, 1)

        self.horizEvent = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizEvent, 1, 1, 1, 1)

        self.cboEvent = QtWidgets.QComboBox()
        self.horizEvent.addWidget(self.cboEvent)

        self.cmdCalculate = QtWidgets.QPushButton()
        self.cmdCalculate.setText('Calculate')
        self.cmdCalculate.clicked.connect(self.cmdCalculate_clicked)
        self.cmdCalculate.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.horizEvent.addWidget(self.cmdCalculate, 0)

        self.lblSegment = QtWidgets.QLabel()
        self.lblSegment.setText('Riverscape Segment')
        self.grid.addWidget(self.lblSegment, 2, 0, 1, 1)

        self.cboSegment = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboSegment, 2, 1, 1, 1)

        self.horiz = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz)

        self.spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horiz.addItem(self.spacerItem)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.vert.addWidget(self.table)

        self.setWidget(self.dockWidgetContents)
