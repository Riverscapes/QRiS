# dialog that sets the analysis units for the analysis

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QLabel, QComboBox

from ..model.analysis import Analysis
from ..lib.unit_conversion import distance_units, area_units, ratio_units, short_unit_name
from .utilities import add_standard_form_buttons

class FrmAnalysisUnits(QDialog):
    
        def __init__(self, parent, analysis: Analysis, ):
            super().__init__(parent)
    
            self.analysis = analysis
    
            self.setWindowTitle('Analysis Units')
            self.setupUI()

        def accept(self):
            self.analysis.units['distance'] = self.cmbDistanceUnits.currentText()
            self.analysis.units['area'] = self.cmbAreaUnits.currentText()
            self.analysis.units['ratio'] = self.cmbRatioUnits.currentText()
            super().accept()
            
        def setupUI(self):
            
            self.vert = QVBoxLayout()
            self.setLayout(self.vert)

            self.grid = QGridLayout()
            self.vert.addLayout(self.grid)

            self.lblDistanceUnits = QLabel('Distance Units')
            self.grid.addWidget(self.lblDistanceUnits , 0, 0, 1, 1)

            self.cmbDistanceUnits = QComboBox()
            self.cmbDistanceUnits.addItems([unit for unit in distance_units])
            self.cmbDistanceUnits.setCurrentText(self.analysis.units['distance'])
            self.grid.addWidget(self.cmbDistanceUnits, 0, 1, 1, 1)

            self.lblAreaUnits = QLabel('Area Units')
            self.grid.addWidget(self.lblAreaUnits , 1, 0, 1, 1)

            self.cmbAreaUnits = QComboBox()
            self.cmbAreaUnits.addItems([unit for unit in area_units])
            self.cmbAreaUnits.setCurrentText(self.analysis.units['area'])
            self.grid.addWidget(self.cmbAreaUnits, 1, 1, 1, 1)

            self.lblRatioUnits = QLabel('Ratio Units')
            self.grid.addWidget(self.lblRatioUnits , 2, 0, 1, 1)

            self.cmbRatioUnits = QComboBox()
            self.cmbRatioUnits.addItems([unit for unit in ratio_units])
            self.cmbRatioUnits.setCurrentText(self.analysis.units['ratio'])
            self.grid.addWidget(self.cmbRatioUnits, 2, 1, 1, 1)


            self.vert.addLayout(add_standard_form_buttons(self, 'analyses'))

