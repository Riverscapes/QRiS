import os
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import Qgis, QgsMessageLog
from qgis.utils import iface

from ..model.project import Project
from ..model.metric_value import MetricValue
from ..model.metric import Metric
from ..model.analysis import Analysis
from ..model.event import Event

from .frm_layer_metric_details import FrmLayerMetricDetails
from .utilities import add_standard_form_buttons
from ..gp import analysis_metrics
from ..gp.analysis_metrics import normalization_factor
from ..QRiS.settings import CONSTANTS
from ..QRiS.path_utilities import parse_posix_path

UNCERTAINTY_NONE = 'None'
UNCERTAINTY_PLUS_MINUS = 'Plus/Minus'
UNCERTAINTY_PERCENT = 'Percent'
UNCERTAINTY_MINMAX = 'Min/Max'


class FrmMetricValue(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, metrics, analysis: Analysis, event: Event, sample_frame_id: int, metric_value: MetricValue):
        super().__init__(parent)
        self.setupUi()

        self.setWindowTitle('Analysis Metric Value')

        # hide these for now
        self.cmdNext.setVisible(False)
        self.cmdPrevious.setVisible(False)

        self.metric_value = metric_value
        self.qris_project = project
        self.analysis = analysis
        self.data_capture_event = event
        self.sample_frame_id = sample_frame_id

        metric_name_text = f'{metric_value.metric.name} ({self.qris_project.units[metric_value.metric.default_unit_id].display})' if metric_value.metric.default_unit_id is not None else f'{metric_value.metric.name}'
        self.txtMetric.setText(metric_name_text)

        if metric_value.metric.min_value is not None:
            self.valManual.setMinimum(metric_value.metric.min_value)
        if metric_value.metric.max_value is not None:
            self.valManual.setMaximum(metric_value.metric.max_value)
        if metric_value.metric.precision is not None:
            self.valManual.setDecimals(metric_value.metric.precision)
        else:
            self.valManual.setDecimals(0)

        if metric_value.manual_value is not None:
            self.valManual.setValue(metric_value.manual_value)

        self.rdoManual.setChecked(metric_value.is_manual)
        self.valManual.setEnabled(self.rdoManual.isChecked())

        if metric_value.automated_value is not None:
            self.txtAutomated.setText(f'{metric_value.automated_value: .{self.metric_value.metric.precision}f}'if isinstance(metric_value.automated_value, float) and self.metric_value.metric.precision is not None else str(metric_value.automated_value))
        self.rdoAutomated.setEnabled(metric_value.automated_value is not None)

        self.rdoAutomated.setChecked(not metric_value.is_manual)

        self.txtDescription.setPlainText(metric_value.description)

        if self.metric_value.uncertainty is not None:
            self.load_uncertainty()
        self.ManualUncertaintyChange()

        if metric_value.is_manual:
            self.valManual.setFocus()
        else:
            self.txtAutomated.setFocus()

        # disable the automated value if unable to calculate
        if not self.metric_value.metric.can_calculate_automated(self.qris_project, self.data_capture_event.id, self.analysis.id):
            self.rdoAutomated.setEnabled(False)
            self.cmdCalculate.setEnabled(False)
            self.txtAutomated.setPlaceholderText('Unable to calculate automated value due to missing required layer(s)')
            self.rdoManual.setChecked(True)
            self.rdoManual.setEnabled(True)
            self.valManual.setFocus()
        else:
            self.rdoAutomated.setEnabled(True)
            self.cmdCalculate.setEnabled(True)

    def rdoManual_checkchanged(self):
        self.valManual.setEnabled(self.rdoManual.isChecked())

    def accept(self):

        self.metric_value.manual_value = self.valManual.value()
        # self.metric_value.automated_value = float(self.txtAutomated.text()) if len(self.txtAutomated.text()) > 0 else None
        self.metric_value.is_manual = self.rdoManual.isChecked()
        self.metric_value.description = self.txtDescription.toPlainText()

        # Save manual unertainty, even if automated metrics are selected
        if self.cboManualUncertainty.currentText() == UNCERTAINTY_NONE:
            self.metric_value.uncertainty = None
        elif self.cboManualUncertainty.currentText() == UNCERTAINTY_MINMAX:
            if self.ValManualUncertaintyMin.value() > self.ValManualUncertaintyMax.value():
                QtWidgets.QMessageBox.warning(self, 'Error Saving Metric Value', 'Min uncertainty value cannot be greater than max uncertainty value')
                return
            if self.metric_value.manual_value is not None and (self.metric_value.manual_value < self.ValManualUncertaintyMin.value() or self.metric_value.manual_value > self.ValManualUncertaintyMax.value()):
                QtWidgets.QMessageBox.warning(self, 'Error Saving Metric Value', 'Manual value must be within the uncertainty range')
                return
            self.metric_value.uncertainty = {self.cboManualUncertainty.currentText(): (self.ValManualUncertaintyMin.value(), self.ValManualUncertaintyMax.value())}
        else:
            self.metric_value.uncertainty = {self.cboManualUncertainty.currentText(): self.ValManualPlusMinus.value()}

        try:
            self.metric_value.save(self.qris_project.project_file, self.analysis, self.data_capture_event, self.sample_frame_id)
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self, 'Error Saving Metric Value', str(ex))
            return

        super().accept()

    def cmd_previous_metric_clicked(self):

        print('TODO')

    def cmd_next_metric_clicked(self):
        print('TODO')

    def ManualUncertaintyChange(self):

        if self.cboManualUncertainty.currentText() == UNCERTAINTY_NONE:
            self.ValManualUncertaintyMin.setVisible(False)
            self.ValManualUncertaintyMax.setVisible(False)
            self.ValManualUncertaintyLabelMin.setVisible(False)
            self.ValManualUncertaintyLabelMax.setVisible(False)
            self.ValManualPlusMinus.setVisible(False)
        else:
            plus_minus = self.cboManualUncertainty.currentText() == UNCERTAINTY_MINMAX

            self.ValManualUncertaintyMin.setVisible(plus_minus)
            self.ValManualUncertaintyMax.setVisible(plus_minus)
            self.ValManualUncertaintyLabelMin.setVisible(plus_minus)
            self.ValManualUncertaintyLabelMax.setVisible(plus_minus)

            self.ValManualPlusMinus.setVisible(not plus_minus)

    def load_uncertainty(self):

        if self.metric_value.uncertainty is None:
            self.cboManualUncertainty.setCurrentText(UNCERTAINTY_NONE)
        elif self.metric_value.uncertainty.get('Min/Max') is not None:
            self.cboManualUncertainty.setCurrentText(UNCERTAINTY_MINMAX)
            self.ValManualUncertaintyMin.setValue(self.metric_value.uncertainty['Min/Max'][0])
            self.ValManualUncertaintyMax.setValue(self.metric_value.uncertainty['Min/Max'][1])
        elif self.metric_value.uncertainty.get('Plus/Minus') is not None:
            self.cboManualUncertainty.setCurrentText(UNCERTAINTY_PLUS_MINUS)
            self.ValManualPlusMinus.setValue(self.metric_value.uncertainty['Plus/Minus'])
        elif self.metric_value.uncertainty.get('Percent') is not None:
            self.cboManualUncertainty.setCurrentText(UNCERTAINTY_PERCENT)
            self.ValManualPlusMinus.setValue(self.metric_value.uncertainty['Percent'])
        else:
            self.cboManualUncertainty.setCurrentText(UNCERTAINTY_NONE)

    def cmd_calculate_metric_clicked(self):

        if self.metric_value.metric.metric_function is None:
            QtWidgets.QMessageBox.warning(self, 'Error Calculating Metric', 'No metric calculation function defined.')
            return

        # modify metric params as needed.
        metric_params: dict = self.metric_value.metric.metric_params
        analysis_params = {}
        if 'centerline' in self.analysis.metadata:
            analysis_params['centerline'] = self.qris_project.profiles[self.analysis.metadata['centerline']]
        if 'dem' in self.analysis.metadata:
            analysis_params['dem'] = self.qris_project.rasters[self.analysis.metadata['dem']]
        if 'valley_bottom' in self.analysis.metadata:
            analysis_params['valley_bottom'] = self.qris_project.valley_bottoms[self.analysis.metadata['valley_bottom']]

        metric_calculation = getattr(analysis_metrics, self.metric_value.metric.metric_function)
        try:
            result = metric_calculation(self.qris_project.project_file, self.sample_frame_id, self.data_capture_event.id, metric_params, analysis_params)
            self.metric_value.automated_value = result
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self, f'Error Calculating Metric', f'{ex}\n\nSee log for additional details.')
            QgsMessageLog.logMessage(str(traceback.format_exc()), f'QRiS_Metrics', level=Qgis.Warning)
            self.txtAutomated.setText(None)
            self.rdoManual.setChecked(True)
            self.rdoAutomated.setEnabled(False)
            return

        self.txtAutomated.setText(f'{result: .{self.metric_value.metric.precision}f}'if isinstance(result, float) and self.metric_value.metric.precision is not None else str(result))
        self.rdoAutomated.setChecked(True)
        self.rdoAutomated.setEnabled(True)

    def setupUi(self):

        self.resize(500, 200)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblMetric = QtWidgets.QLabel()
        self.lblMetric.setText('Metric')
        self.grid.addWidget(self.lblMetric, 0, 0, 1, 1)

        self.txtMetric = QtWidgets.QLineEdit()
        self.txtMetric.setReadOnly(True)
        self.grid.addWidget(self.txtMetric, 0, 1, 1, 1)

        self.cmdHelp = QtWidgets.QPushButton()
        self.cmdHelp.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/help'))
        self.cmdHelp.setToolTip('Help')
        self.cmdHelp.clicked.connect(lambda: FrmLayerMetricDetails(self, self.qris_project, metric=self.metric_value.metric).exec_())
        self.grid.addWidget(self.cmdHelp, 0, 2, 1, 1)

        self.horizMetric = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizMetric, 0, 2, 1, 1)

        self.cmdPrevious = QtWidgets.QPushButton()
        # self.cmdPrevious.setText('Previous Metric')
        self.cmdPrevious.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/arrow_up'))
        self.cmdPrevious.clicked.connect(self.cmd_previous_metric_clicked)
        self.cmdPrevious.setToolTip('Save Changes and Move to Previous Metric')
        self.horizMetric.addWidget(self.cmdPrevious)

        self.cmdNext = QtWidgets.QPushButton()
        # self.cmdNext.setText('Next Metric')
        self.cmdNext.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/arrow_down'))
        self.cmdNext.setToolTip('Save Changes and Move to Next Metric')
        self.cmdNext.clicked.connect(self.cmd_next_metric_clicked)
        self.horizMetric.addWidget(self.cmdNext)

        self.rdoManual = QtWidgets.QRadioButton()
        self.rdoManual.setChecked(True)
        self.rdoManual.setText('Manual Value')
        self.rdoManual.toggled.connect(self.rdoManual_checkchanged)
        self.grid.addWidget(self.rdoManual, 1, 0, 1, 1)

        self.horiz_manual = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz_manual, 1, 1, 1, 1)

        self.valManual = QtWidgets.QDoubleSpinBox()
        self.horiz_manual.addWidget(self.valManual)

        self.lblUbcertainty = QtWidgets.QLabel()
        self.lblUbcertainty.setText('Uncertainty')
        self.horiz_manual.addWidget(self.lblUbcertainty)

        self.cboManualUncertainty = QtWidgets.QComboBox()
        self.cboManualUncertainty.addItems([UNCERTAINTY_NONE, UNCERTAINTY_PLUS_MINUS, UNCERTAINTY_PERCENT, UNCERTAINTY_MINMAX])
        self.horiz_manual.addWidget(self.cboManualUncertainty)
        self.cboManualUncertainty.currentIndexChanged.connect(self.ManualUncertaintyChange)

        self.ValManualPlusMinus = QtWidgets.QDoubleSpinBox()
        self.horiz_manual.addWidget(self.ValManualPlusMinus)

        self.ValManualUncertaintyLabelMin = QtWidgets.QLabel()
        self.ValManualUncertaintyLabelMin.setText('Minimum')
        self.horiz_manual.addWidget(self.ValManualUncertaintyLabelMin)

        self.ValManualUncertaintyMin = QtWidgets.QDoubleSpinBox()
        self.horiz_manual.addWidget(self.ValManualUncertaintyMin)

        self.ValManualUncertaintyLabelMax = QtWidgets.QLabel()
        self.ValManualUncertaintyLabelMax.setText('Maximum')
        self.horiz_manual.addWidget(self.ValManualUncertaintyLabelMax)

        self.ValManualUncertaintyMax = QtWidgets.QDoubleSpinBox()
        self.horiz_manual.addWidget(self.ValManualUncertaintyMax)

        self.rdoAutomated = QtWidgets.QRadioButton()
        self.rdoAutomated.setText('Automated Value')
        self.grid.addWidget(self.rdoAutomated, 2, 0, 1, 1)

        self.txtAutomated = QtWidgets.QLineEdit()
        self.txtAutomated.setReadOnly(True)
        self.grid.addWidget(self.txtAutomated, 2, 1, 1, 1)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)

        self.cmdCalculate = QtWidgets.QPushButton()
        # self.cmdCalculate.setText('Calculate')
        self.cmdCalculate.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/calculate'))
        self.cmdCalculate.setToolTip('Calculate Metric From GIS')
        self.cmdCalculate.setSizePolicy(sizePolicy)
        self.cmdCalculate.clicked.connect(self.cmd_calculate_metric_clicked)
        self.grid.addWidget(self.cmdCalculate, 2, 2, 1, 1)

        # self.lblUncertainty = QtWidgets.QLabel()
        # self.lblUncertainty.setText('Uncertainty')
        # self.grid.addWidget(self.lblUncertainty, 3, 0, 1, 1)

        self.tab = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tab)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tab.addTab(self.txtDescription, 'Description')

        self.metadata = QtWidgets.QTableWidget()
        self.tab.addTab(self.metadata, 'Metadata')

        self.vert.addLayout(add_standard_form_buttons(self, 'analyses'))
