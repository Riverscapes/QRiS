

import os
from PyQt5 import QtCore, QtGui, QtWidgets

from ..QRiS.units import get_areas, get_lengths

from ..model.project import Project


from .utilities import add_standard_form_buttons


class FrmOptions(QtWidgets.QDialog):

    def __init__(self, parent, project: Project):
        super().__init__(parent)
        self.setupUi()

        self.qris_project = project

        for control, data in ((self.cboLength, get_lengths), (self.cboArea, get_areas)):
            for display_name, unit_key in data().items():
                # item = QtGui.QStandardItem(display_name)
                # item.setData(unit_key, QtCore.Qt.UserRole)
                control.addItem(display_name, unit_key)

        # self.setWindowTitle(f'Geospatial Metrics for {self.mask.name}')

        # self.txtMask.setText(self.mask.name)

        # self.load_tree()

    def accept(self):

        super().accept()

    def setupUi(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblLength = QtWidgets.QLabel()
        self.lblLength.setText('Length')
        self.grid.addWidget(self.lblLength, 0, 0, 1, 1)

        self.cboLength = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboLength, 0, 1, 1, 1)

        self.lblArea = QtWidgets.QLabel()
        self.lblArea.setText('Area')
        self.grid.addWidget(self.lblArea, 1, 0, 1, 1)

        self.cboArea = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboArea, 1, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'zonal_statistics'))
