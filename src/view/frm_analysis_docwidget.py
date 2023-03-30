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

import os
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import Qgis, QgsMessageLog
from qgis.utils import iface

from .frm_analysis_properties import FrmAnalysisProperties

# from qgis.core import QgsMapLayer
# from qgis.gui import QgsDataSourceSelectDialog
# from qgis.utils import iface

from ..model.project import Project
from ..model.analysis import ANALYSIS_MACHINE_CODE, Analysis
from ..model.analysis_metric import AnalysisMetric
from ..model.db_item import DB_MODE_CREATE, DB_MODE_IMPORT, DBItem, DBItemModel
from ..model.event import EVENT_MACHINE_CODE, Event
from ..model.raster import BASEMAP_MACHINE_CODE, Raster
from ..model.mask import MASK_MACHINE_CODE, AOI_MASK_TYPE_ID, Mask, get_sample_frame_ids
from ..model.metric_value import MetricValue, load_metric_values, print_uncertanty
from ..gp import analysis_metrics
from ..gp.analysis_metrics import MetricInputMissingError

from .frm_metric_value import FrmMetricValue
from .frm_calculate_all_metrics import FrmCalculateAllMetrics


class FrmAnalysisDocWidget(QtWidgets.QDockWidget):

    def __init__(self, parent):

        super(FrmAnalysisDocWidget, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose)
        self.setupUi()

    def configure_analysis(self, project: Project, analysis: Analysis, event: Event):

        self.project = project
        self.analysis = analysis
        self.txtName.setText(analysis.name)

        # Set Sample Frames
        frame_ids = get_sample_frame_ids(self.project.project_file, self.analysis.mask.id)
        self.segments_model = DBItemModel(frame_ids)
        self.cboSampleFrame.setModel(self.segments_model)

        # Events
        self.events_model = DBItemModel(project.events)
        self.cboEvent.setModel(self.events_model)

        # Build the metric table (this will also load the metric values)
        self.build_table()

    def build_table(self):

        self.table.clearContents()
        self.table.setHorizontalHeaderLabels(['Metric', 'Value', 'Uncertainty', 'Status'])
        self.table.setColumnWidth(0, self.table.width() * 0.8)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 50)
        self.table.setIconSize(QtCore.QSize(32, 16))

        self.table.setRowCount(0)
        analysis_metrics = list(metric for metric in self.analysis.analysis_metrics.values() if metric.level_id == 1) if self.rdoMetrics.isChecked() else list(self.analysis.analysis_metrics.values())
        self.table.setRowCount(len(analysis_metrics))
        for row in range(len(analysis_metrics)):
            metric = analysis_metrics[row]
            label_metric = QtWidgets.QTableWidgetItem()
            metric_text = f'{metric.metric.name} ({self.project.units[metric.metric.default_unit_id].display})' if metric.metric.default_unit_id is not None else f'{metric.metric.name}'
            label_metric.setText(metric_text)
            self.table.setItem(row, 0, label_metric)
            label_metric.setData(QtCore.Qt.UserRole, metric)
            label_metric.setFlags(QtCore.Qt.ItemIsEnabled)

            label_value = QtWidgets.QTableWidgetItem()
            self.table.setItem(row, 1, label_value)

            label_uncertainty = QtWidgets.QTableWidgetItem()
            self.table.setItem(row, 2, label_uncertainty)

            status_item = QtWidgets.QTableWidgetItem()
            self.table.setItem(row, 3, status_item)

        self.table.doubleClicked.connect(self.edit_metric_value)

        self.load_table_values()

    def load_table_values(self):

        event = self.cboEvent.currentData(QtCore.Qt.UserRole)
        mask_feature_id = self.cboSampleFrame.currentData(QtCore.Qt.UserRole).id

        if event is not None and mask_feature_id is not None:
            # Load latest metric values from DB
            metric_values = load_metric_values(self.project.project_file, self.analysis, event, mask_feature_id, self.project.metrics)

            # Loop over active metrics and load values into grid
            for row in range(self.table.rowCount()):

                metric = self.table.item(row, 0).data(QtCore.Qt.UserRole)
                metric_value_text = ''
                uncertainty_text = ''
                self.set_status(row)
                self.table.item(row, 1).setData(QtCore.Qt.UserRole, None)
                if metric.metric.id in metric_values:
                    metric_value = metric_values[metric.metric.id]
                    metric_value_text = metric_value.manual_value if metric_value.is_manual else metric_value.automated_value
                    uncertainty_text = print_uncertanty(metric_value.uncertainty) if metric_value.is_manual else None
                    self.table.item(row, 1).setData(QtCore.Qt.UserRole, metric_value)
                    self.set_status(row, metric_value)
                self.table.item(row, 1).setText(f'{metric_value_text: .2f}'if isinstance(metric_value_text, float) else str(metric_value_text))
                self.table.item(row, 2).setText(str(uncertainty_text))

    def set_status(self, row, metric_value: MetricValue = None):

        status_item = self.table.item(row, 3)
        # Default Status none exists or selected
        status_manual_icon = QtGui.QPixmap(':/plugins/qris_toolbar/manual_none')
        status_auto_icon = QtGui.QPixmap(':/plugins/qris_toolbar/auto_none')

        if metric_value is not None:
            # set icons for value existence
            if metric_value.manual_value is not None:
                status_manual_icon = QtGui.QPixmap(':/plugins/qris_toolbar/manual_exists')
            if metric_value.automated_value is not None:
                status_auto_icon = QtGui.QPixmap(':/plugins/qris_toolbar/auto_exists')
            # set icons for value selection
            if metric_value.is_manual and metric_value.manual_value is not None:
                status_manual_icon = QtGui.QPixmap(':/plugins/qris_toolbar/manual_selected')
                if metric_value.automated_value is not None:
                    # set warining icon if manual value is more than 10% different from automated value
                    if abs(metric_value.manual_value - metric_value.automated_value) > 0.1 * metric_value.automated_value:
                        status_manual_icon = QtGui.QPixmap(':/plugins/qris_toolbar/manual_selected_warning')
            if not metric_value.is_manual and metric_value.automated_value is not None:
                status_auto_icon = QtGui.QPixmap(':/plugins/qris_toolbar/auto_selected')

        icon = QtGui.QIcon()
        icon.actualSize(QtCore.QSize(32, 16))
        pixmap = QtGui.QPixmap(32, 16)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter()
        painter.begin(pixmap)
        painter.setBackgroundMode(QtCore.Qt.TransparentMode)
        painter.drawPixmap(0, 0, status_manual_icon)
        painter.drawPixmap(16, 0, status_auto_icon)
        icon.addPixmap(pixmap)
        status_item.setIcon(icon)
        painter = None

    def cmdCalculate_clicked(self):

        frm = FrmCalculateAllMetrics(self)
        result = frm.exec_()

        if result == QtWidgets.QDialog.Accepted:
            mask_features = [self.cboSampleFrame.itemData(i, QtCore.Qt.UserRole) for i in range(self.cboSampleFrame.count())] if frm.rdoAllSF.isChecked() else [self.cboSampleFrame.currentData(QtCore.Qt.UserRole)]
            data_capture_events = [self.cboEvent.itemData(i, QtCore.Qt.UserRole) for i in range(self.cboEvent.count())] if frm.rdoAllDCE.isChecked() else [self.cboEvent.currentData(QtCore.Qt.UserRole)]

            errors = False
            missing_data = False
            for mask_feature in mask_features:
                for data_capture_event in data_capture_events:
                    metric_values = load_metric_values(self.project.project_file, self.analysis, data_capture_event, mask_feature.id, self.project.metrics)
                    for analysis_metric in self.analysis.analysis_metrics.values():
                        metric = analysis_metric.metric
                        metric_value = metric_values.get(metric.id, MetricValue(metric, None, None, False, None, None, metric.default_unit_id, None))
                        if metric_value.automated_value is not None and not frm.chkOverwrite.isChecked():
                            continue
                        if metric.metric_function is None:
                            # Metric is not defined in database. continue
                            continue
                        try:
                            if 'rasters' in metric.metric_params:
                                rasters = {}
                                for raster_name in metric.metric_params['rasters']:
                                    raster_id = [k for k, v in self.project.lookup_tables['lkp_raster_types'].items() if v.name == raster_name][0]
                                    project_rasters = [r for r in data_capture_event.rasters if r.raster_type_id == raster_id]
                                    if len(project_rasters) == 0:
                                        raise MetricInputMissingError(f'Required raster {raster_name} for {metric.name} not found in project')
                                    rasters[raster_name] = {'path': os.path.join(os.path.dirname(self.project.project_file), project_rasters[0].path)}
                                metric.metric_params['rasters'] = rasters

                            metric_calculation = getattr(analysis_metrics, metric.metric_function)
                            result = metric_calculation(self.project.project_file, mask_feature.id, data_capture_event.id, metric.metric_params)
                            metric_value.automated_value = result
                            if frm.chkForceActive.isChecked():
                                metric_value.is_manual = False
                            metric_value.save(self.project.project_file, self.analysis, data_capture_event, mask_feature.id, metric.default_unit_id)
                            QgsMessageLog.logMessage(f'Successfully calculated metric {metric.name} for {data_capture_event.name} sample frame {mask_feature.id}', 'QRiS_Metrics', Qgis.Info)
                        except MetricInputMissingError as ex:
                            missing_data = True
                            QgsMessageLog.logMessage(f'Error calculating metric {metric.name}: {ex}', 'QRiS_Metrics', Qgis.Warning)
                            continue
                        except Exception as ex:
                            errors = True
                            QgsMessageLog.logMessage(f'Error calculating metric {metric.name}: {ex}', 'QRiS_Metrics', Qgis.Warning)
                            continue
            if errors is False and missing_data is False:
                iface.messageBar().pushMessage('Metrics', 'All metrics successfully calculated.', level=Qgis.Success)
            else:
                if missing_data is True:
                    iface.messageBar().pushMessage('Metrics', 'One or more metrics were not calculated due to missing data requirements. See log for details.', level=Qgis.Success)
                if errors is True:
                    iface.messageBar().pushMessage('Metrics', 'Onr or more metrics were not calculated due to processing error(s). See log for details.', level=Qgis.Warning)
            self.load_table_values()

    def cmdProperties_clicked(self):

        frm = FrmAnalysisProperties(self, self.project, self.analysis)
        result = frm.exec_()
        if result is not None and result != 0:
            self.txtName.setText(frm.analysis.name)
            self.build_table()

    def edit_metric_value(self, mi):

        metric_value = self.table.item(mi.row(), 1).data(QtCore.Qt.UserRole)
        metric = self.table.item(mi.row(), 0).data(QtCore.Qt.UserRole)
        event = self.cboEvent.currentData(QtCore.Qt.UserRole)
        mask_feature = self.cboSampleFrame.currentData(QtCore.Qt.UserRole)

        if metric_value is None:
            metric_value = MetricValue(metric.metric, None, None, True, None, None, metric.metric.default_unit_id, {})

        frm = FrmMetricValue(self, self.project, self.project.metrics, self.analysis, event, mask_feature.id, metric_value)
        result = frm.exec_()
        if result is not None and result != 0:
            self.load_table_values()

    def resizeEvent(self, event):
        if self.table.columnWidth(0) > self.table.width():
            self.table.setColumnWidth(0, self.table.width() * 0.8)
        QtWidgets.QDockWidget.resizeEvent(self, event)

    def closeEvent(self, event):
        if self.table.receivers(self.table.doubleClicked) > 0:
            self.table.doubleClicked.disconnect()
        QtWidgets.QDockWidget.closeEvent(self, event)

    def setupUi(self):

        self.setWindowTitle('QRiS Analysis')
        self.dockWidgetContents = QtWidgets.QWidget(self)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self.dockWidgetContents)

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
        self.cboEvent.currentIndexChanged.connect(self.load_table_values)
        self.horizEvent.addWidget(self.cboEvent)

        self.cmdCalculate = QtWidgets.QPushButton()
        self.cmdCalculate.setText('Calculate All')
        self.cmdCalculate.clicked.connect(self.cmdCalculate_clicked)
        self.cmdCalculate.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.horizEvent.addWidget(self.cmdCalculate, 0)

        self.lblSegment = QtWidgets.QLabel()
        self.lblSegment.setText('Sample Frame')
        self.grid.addWidget(self.lblSegment, 2, 0, 1, 1)

        self.cboSampleFrame = QtWidgets.QComboBox()
        self.cboSampleFrame.currentIndexChanged.connect(self.load_table_values)
        self.grid.addWidget(self.cboSampleFrame, 2, 1, 1, 1)

        self.lblDisplay = QtWidgets.QLabel('Display Values')
        self.grid.addWidget(self.lblDisplay, 3, 0, 1, 1)

        self.layoutDisplay = QtWidgets.QHBoxLayout()

        self.rdoAll = QtWidgets.QRadioButton('Metrics and Indicators')
        self.rdoAll.setChecked(True)
        self.rdoAll.toggled.connect(self.build_table)
        self.layoutDisplay.addWidget(self.rdoAll)

        self.rdoMetrics = QtWidgets.QRadioButton('Metrics Only')
        self.rdoMetrics.setChecked(False)
        self.layoutDisplay.addWidget(self.rdoMetrics)

        self.layoutDisplay.addStretch(1)
        self.grid.addLayout(self.layoutDisplay, 3, 1, 1, 1)

        self.horiz = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz)

        self.spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horiz.addItem(self.spacerItem)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.vert.addWidget(self.table)

        self.setWidget(self.dockWidgetContents)
