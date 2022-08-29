from PyQt5 import QtCore, QtGui, QtWidgets
from ..model.project import Project
from ..model.metric_value import MetricValue
from ..model.metric import Metric


class FrmMetricValue(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, metrics, metric_value: MetricValue):
        super().__init__(parent)
        self.setupUi()

        self.metric_value = metric_value
        self.project = project
        self.metrics = metrics

        self.txtMetric.setText(metric_value.metric.name)

        self.valManual.setValue(metric_value.manual_value)
        self.rdoManual.setChecked(metric_value.is_manual)
        self.valManual.setEnabled(self.rdoManual.isChecked())

        self.txtAutomated.setText(metric_value.automated_value)
        self.rdoAutomated.setChecked(not metric_value.is_manual)

        self.txtDescription.setPlainText(metric_value.description)

    def rdoManual_checkchanged(self):
        self.valManual.setEnabled(self.rdoManual.isChecked())

    def accept(self):

        self.metric_value.manual_value = self.valManual.value
        self.metric_value.automated_value = float(self.txtAutomated.text())
        self.metric_value.is_manual = self.rdoManual.isChecked()
        self.metric_value.description = self.txtDescription.toPlainText()
        self.metric_value.save()

    def cmd_previous_metric_clicked(self):

        print('TODO')

    def cmd_next_metric_clicked(self):
        print('TODO')

    def setupUi(self):

        self.resize(640, 480)

        self.vert = QtWidgets.QVBoxLayout()
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.rdoManual = QtWidgets.QRadioButton()
        self.rdoManual.setChecked(True)
        self.rdoManual.setText('Manual Value')
        self.rdoManual.toggled.connect(self.rdoManual_checkchanged)
        self.grid.addWidget(self.rdoManual, 0, 0, 1, 1)

        self.lblMetric = QtWidgets.QLabel()
        self.lblMetric.setText('Metric')
        self.grid.addWidget(self.lblMetric, 0, 0, 1, 1)

        self.txtMetric = QtWidgets.QLineEdit()
        self.txtMetric.setReadOnly(True)
        self.grid.addWidget(self.txtMetric, 0, 1, 1, 1)

        self.horizMetric = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horizMetric, 0, 2, 1, 1)

        self.cmdPrevious = QtWidgets.QPushButton()
        self.cmdPrevious.setText('Previous Metric')
        self.cmdPrevious.clicked.connect(self.cmd_previous_metric_clicked)
        self.horizMetric.addWidget(self.cmdPrevious)

        self.cmdNext = QtWidgets.QPushButton()
        self.cmdNext.setText('Next Metric')
        self.cmdNext.clicked.connect(self.cmd_next_metric_clicked)
        self.horizMetric.addWidget(self.cmdNext)

        self.valManual = QtWidgets.QDoubleSpinBox()
        self.grid.addWidget(self.valManual, 0, 1, 1, 1)

        self.rdoAutomated = QtWidgets.QRadioButton()
        self.rdoAutomated.setText('Automated Value')
        self.grid.addWidget(self.rdoAutomated, 1, 0, 1, 1)

        self.txtAutomated = QtWidgets.QLineEdit()
        self.txtAutomated.setReadOnly(True)
        self.grid.addWidget(self.txtAutomated, 1, 1, 1, 1)

        self.cmdCalculate = QtWidgets.QPushButton()
        self.cmdCalculate.setText('Calculate')
        self.grid.addWidget(self.cmdCalculate, 1, 2, 1, 1)

        self.lblUncertainty = QtWidgets.QLabel()
        self.lblUncertainty.setText('Uncertainty')
        self.grid.addWidget(self.lblUncertainty, 2, 0, 1, 1)

        self.valUncertainty = QtWidgets.QDoubleSpinBox()
        self.grid.addWidget(self.valUncertainty, 2, 1, 1, 1)

        self.tab = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tab)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tab.addTab(self.txtDescription, 'Description')

        self.metadata = QtWidgets.QTableWidget()
        self.tab.addTab(self.metadata, 'Metadata')

        self.horiz = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz)

        self.cmdHelp = QtWidgets.QPushButton()
        self.cmdHelp.setText('Help')
        self.horiz.addWidget(self.cmdHelp)

        self.spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horiz.addItem(self.spacerItem)

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.horiz.addWidget(self.buttonBox)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
