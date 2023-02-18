import plistlib
from re import T
from PyQt5 import QtCore, QtGui, QtWidgets
from ..model.project import Project
from ..model.metric_value import MetricValue
from ..model.metric import Metric
from ..model.analysis import Analysis
from ..model.event import Event
from .utilities import add_standard_form_buttons

UNCERTAINTY_NONE = 'None'
UNCERTAINTY_PLUS_MINUS = 'Plus/Minus'
UNCERTAINTY_PERCENT = 'Percent'
UNCERTAINTY_MINMAX = 'Min/Max'


class FrmMetricValue(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, metrics, analysis: Analysis, event: Event, mask_feature_id: int, metric_value: MetricValue):
        super().__init__(parent)
        self.setupUi()

        self.setWindowTitle('Analysis Metric Value')

        # hide these for now
        self.cmdNext.setVisible(False)
        self.cmdPrevious.setVisible(False)

        self.metric_value = metric_value
        self.project = project
        self.analysis = analysis
        self.data_capture_event = event
        self.mask_feature_id = mask_feature_id
        self.metrics = metrics

        self.txtMetric.setText(metric_value.metric.name)

        if metric_value.manual_value is not None:
            self.valManual.setValue(metric_value.manual_value)

        self.rdoManual.setChecked(metric_value.is_manual)
        self.valManual.setEnabled(self.rdoManual.isChecked())

        if metric_value.automated_value is not None:
            self.txtAutomated.setText(metric_value.automated_value)
        self.rdoAutomated.setEnabled(metric_value.automated_value is not None)

        self.rdoAutomated.setChecked(not metric_value.is_manual)

        self.txtDescription.setPlainText(metric_value.description)

        self.ManualUncertaintyChange()

    def rdoManual_checkchanged(self):
        self.valManual.setEnabled(self.rdoManual.isChecked())

    def accept(self):

        self.metric_value.manual_value = self.valManual.value()
        self.metric_value.automated_value = float(self.txtAutomated.text()) if len(self.txtAutomated.text()) > 0 else None
        self.metric_value.is_manual = self.rdoManual.isChecked()
        self.metric_value.description = self.txtDescription.toPlainText()
        try:
            self.metric_value.save(self.project.project_file, self.analysis, self.data_capture_event, self.mask_feature_id)
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
        self.cmdCalculate.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/gis'))
        self.cmdCalculate.setToolTip('Calculate Metric From GIS')
        self.cmdCalculate.setSizePolicy(sizePolicy)
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

        self.vert.addLayout(add_standard_form_buttons(self, 'metric_Value'))
