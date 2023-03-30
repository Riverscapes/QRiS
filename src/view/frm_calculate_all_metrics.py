from PyQt5 import QtCore, QtGui, QtWidgets
from qgis import core, gui, utils

from .utilities import add_standard_form_buttons


class FrmCalculateAllMetrics(QtWidgets.QDialog):

    def __init__(self, parent):
        super(FrmCalculateAllMetrics, self).__init__(parent)
        self.setupUi()

    def accept(self):

        super(FrmCalculateAllMetrics, self).accept()

    def setupUi(self):

        self.setMinimumSize(500, 300)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        # Groupbox named "Data Capture Events" with radio buttons for "just the currently active DCE" or "All Data Capture Events"
        self.grpDCE = QtWidgets.QGroupBox('Data Capture Events')
        self.rdoActiveDCE = QtWidgets.QRadioButton('Just the currently active DCE')
        self.rdoAllDCE = QtWidgets.QRadioButton('All Data Capture Events')
        self.rdoActiveDCE.setChecked(True)
        self.grpDCE.setLayout(QtWidgets.QVBoxLayout())
        self.grpDCE.layout().addWidget(self.rdoActiveDCE)
        self.grpDCE.layout().addWidget(self.rdoAllDCE)
        self.vert.addWidget(self.grpDCE)

        # groupbox named Sampling Frames with radio buttons for "just the currently active SF" or "All Sampling Frames"
        self.grpSF = QtWidgets.QGroupBox('Sampling Frames')
        self.rdoActiveSF = QtWidgets.QRadioButton('Just the currently active SF')
        self.rdoAllSF = QtWidgets.QRadioButton('All Sampling Frames')
        self.rdoActiveSF.setChecked(True)
        self.grpSF.setLayout(QtWidgets.QVBoxLayout())
        self.grpSF.layout().addWidget(self.rdoActiveSF)
        self.grpSF.layout().addWidget(self.rdoAllSF)
        self.vert.addWidget(self.grpSF)

        # groupbox named metric values with check boxes for "overwrite any existing autmated values" and "force automated values to be the active values"
        self.grpMetricValues = QtWidgets.QGroupBox('Metric Values')
        self.chkOverwrite = QtWidgets.QCheckBox('Overwrite any existing automated values')
        self.chkForceActive = QtWidgets.QCheckBox('Force automated values to be the active values')
        self.grpMetricValues.setLayout(QtWidgets.QVBoxLayout())
        self.grpMetricValues.layout().addWidget(self.chkOverwrite)
        self.grpMetricValues.layout().addWidget(self.chkForceActive)
        self.vert.addWidget(self.grpMetricValues)

        self.vert.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        self.vert.addLayout(add_standard_form_buttons(self, 'metrics'))
