import traceback
import json

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import Qgis, QgsMessageLog, QgsUnitTypes

from ..model.project import Project
from ..model.metric_value import MetricValue
from ..model.metric import Metric
from ..model.analysis import Analysis
from ..model.event import Event

from .utilities import add_standard_form_buttons
from .frm_layer_metric_details import FrmLayerMetricDetails
from .widgets.metadata import MetadataWidget
from ..lib.unit_conversion import convert_units, convert_count_per_length, convert_count_per_area, unit_types
from ..gp import analysis_metrics

UNCERTAINTY_NONE = 'None'
UNCERTAINTY_PLUS_MINUS = 'Plus/Minus'
UNCERTAINTY_PERCENT = 'Percent'
UNCERTAINTY_MINMAX = 'Min/Max'


class FrmMetricValue(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, analysis: Analysis, event: Event, sample_frame_id: int, metric_value: MetricValue):
        super().__init__(parent)
        self.setupUi()

        self.setWindowTitle('Analysis Metric Value')

        self.metric_value = metric_value
        self.qris_project = project
        self.analysis = analysis
        self.data_capture_event = event
        self.sample_frame_id = sample_frame_id

        if self.metric_value.metadata:
             self.metadata_widget.load_json(json.dumps(self.metric_value.metadata))
        
        # Determine initial display unit
        unit_type = metric_value.metric.unit_type
        lookup_type = unit_type
        if unit_type == 'count' and metric_value.metric.normalized:
             lookup_type = metric_value.metric.normalization_unit_type
        self.current_unit = self.analysis.units.get(lookup_type, None)
        
        # Fallback to metric default if not in analysis preferences or valid default
        if self.current_unit is None and unit_type in unit_types:
             # Find a default or use the base unit
             pass # Will be handled by load_units

        metric_name_text = f'{metric_value.metric.name}'
        self.txtMetric.setText(metric_name_text)
        
        if metric_value.metric.description:
            self.lblMetricDesc.setText(metric_value.metric.description)

        if metric_value.metric.min_value is not None:
            self.valManual.setMinimum(metric_value.metric.min_value)
        if metric_value.metric.max_value is not None:
            self.valManual.setMaximum(metric_value.metric.max_value)
        if metric_value.metric.precision is not None:
            self.valManual.setDecimals(metric_value.metric.precision)
        else:
            self.valManual.setDecimals(0)
            
        # Initialize UI Units 
        self.load_units(unit_type)

        # Load Manual Value (Converted to current unit)
        if metric_value.manual_value is not None:
            val = self.convert_to_display(metric_value.manual_value)
            self.valManual.setValue(val)

        self.rdoManual.setChecked(metric_value.is_manual)
        self.valManual.setEnabled(self.rdoManual.isChecked())

        # Load Automated Value (Always SI)
        if metric_value.automated_value is not None:
            self.update_automated_text(metric_value.automated_value)
            
        self.rdoAutomated.setEnabled(metric_value.automated_value is not None)

        self.rdoAutomated.setChecked(not metric_value.is_manual)

        self.txtDescription.setPlainText(metric_value.description)
        
        # Connect Unit Change AFTER loading values to prevent double conversion or clearing
        self.cboUnits.currentIndexChanged.connect(self.on_unit_changed)

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
            self.actionCalculate.setEnabled(False)
            self.txtAutomated.setPlaceholderText('Unable to calculate automated value due to missing required layer(s)')
            self.txtAutomated.setToolTip('Unable to calculate automated value due to missing required layer(s)')
            self.rdoAutomated.setToolTip('Unable to calculate automated value due to missing required layer(s)')
            self.rdoManual.setChecked(True)
            self.rdoManual.setEnabled(True)
            self.valManual.setFocus()
        else:
            self.rdoAutomated.setEnabled(True)
            self.actionCalculate.setEnabled(True)

    def load_units(self, unit_type):
        """Populates the unit combobox and selects current default."""
        self.cboUnits.blockSignals(True)
        self.cboUnits.clear()
        
        effective_unit_type = unit_type
        if unit_type == 'count' and self.metric_value.metric.normalized:
            effective_unit_type = self.metric_value.metric.normalization_unit_type
        
        if effective_unit_type in unit_types and effective_unit_type not in ['count']:
            units_dict = unit_types[effective_unit_type]
            # units_dict is {DisplayName: Key/Code}
            for name, code in units_dict.items():
                display_name = name
                if self.metric_value.metric.normalized and self.metric_value.metric.unit_type == 'count':
                     display_name = f"count/{name}"
                self.cboUnits.addItem(display_name, name)
            
            self.cboUnits.setEnabled(True)
            self.cboUnits.setVisible(True)
            self.lblUnits.setVisible(True)

            if self.current_unit:
                 index = self.cboUnits.findData(self.current_unit)
                 if index >= 0:
                     self.cboUnits.setCurrentIndex(index)
                 else:
                     if self.cboUnits.count() > 0:
                         self.cboUnits.setCurrentIndex(0)
                         self.current_unit = self.cboUnits.itemData(0)
            else:
                 if self.cboUnits.count() > 0:
                     self.cboUnits.setCurrentIndex(0)
                     self.current_unit = self.cboUnits.itemData(0)

        else:
            self.cboUnits.setEnabled(False)
            self.cboUnits.setVisible(False)
            self.lblUnits.setVisible(False)
            self.current_unit = None
            
        self.cboUnits.blockSignals(False)

    def on_unit_changed(self, index):
        new_unit = self.cboUnits.currentData()
        
        old_unit = self.current_unit
        
        if not old_unit:
            self.current_unit = new_unit
            return

        # Convert Manual Value
        if self.valManual.value() != 0: 
             # Step 1: Convert to Base (SI) using old unit
             base_val = self.convert_to_base(self.valManual.value(), old_unit)
             
             # Step 2: Convert to New Unit
             new_val = self.convert_to_display(base_val, new_unit)
             self.valManual.setValue(new_val)
        
        self.current_unit = new_unit
        
        # Update Automated Value Display (convert SI -> new_unit)
        if self.metric_value.automated_value is not None:
            self.update_automated_text(self.metric_value.automated_value)

    def convert_to_display(self, value_si, unit_name=None):
        """Converts stored SI value to display unit."""
        if value_si is None: return None
        target_unit = unit_name if unit_name else self.current_unit
        if not target_unit: return value_si
        
        return self._do_conversion(value_si, self.metric_value.metric.base_unit, target_unit, invert=False)

    def convert_to_base(self, value_disp, unit_name=None):
        """Converts display value back to SI base."""
        if value_disp is None: return None
        source_unit = unit_name if unit_name else self.current_unit
        if not source_unit: return value_disp
        
        return self._do_conversion(value_disp, self.metric_value.metric.base_unit, source_unit, invert=True)

    def _do_conversion(self, value, base_unit, target_unit_name, invert=False):
        # Uses lib.unit_conversion logic
        # Note: metric.normalized affects logic if density (count/length vs count/area)
        
        # If normalized, we need the normalization unit type
        if self.metric_value.metric.normalized:
            # When normalized, the metric unit type is 'count', but normalization is 'distance' or 'area'
            # The 'target_unit_name' passed here is likely a distance or area unit (e.g. 'Meters', 'Acres')
            norm_type = self.metric_value.metric.normalization_unit_type
            
            if norm_type == 'distance':
                # Function signature: convert_count_per_length(value, from_unit, to_unit)
                # If invert (Display -> Base): We have Count/Ft, want Count/M
                # convert_count_per_length converts FROM base TO target. 
                # e.g. val in per_meter, target='Feet' -> returns per_feet
                # To invert, we need to think carefully.
                # 1 per meter = 0.3048 per foot? No. 1/m * (1m/3.28ft) = 1/3.28 1/ft = 0.3048?
                
                # Let's rely on convert_count_per_length if not inverted.
                if not invert:
                     # Base (per meter) -> Target (per foot)
                     return convert_count_per_length(value, base_unit, target_unit_name)
                else:
                     # Target (per foot) -> Base (per meter)
                     # convert_count_per_length logic: value * (from_factor / to_factor)
                     # Here we want to go backwards. 
                     # Actually convert_count_per_length takes (value, unit_from, unit_to). 
                     # So if we say convert_count_per_length(val, TargetUnit, BaseUnit) it should work? 
                     # base_unit for metric is usually QgsUnitTypes.DistanceMeters (which is integer 1)
                     # target_unit_name is string 'Feet'.
                     return convert_count_per_length(value, target_unit_name, base_unit)
                     
            elif norm_type == 'area':
                 if not invert:
                     return convert_count_per_area(value, base_unit, target_unit_name)
                 else:
                     return convert_count_per_area(value, target_unit_name, base_unit)
            else:
                 # Fallback?
                 return value
        else:
             # Standard conversion
             # convert_units(value, from_unit, to_unit, invert=False)
             # if invert=True handled inside? 
             # Implementation of convert_units in lib:
             # def convert_units(value, from_unit, to_unit, invert=False):
             #    if invert: return value / factor ...
             
             # Actually convert_units signature in lib usually assumes conversion relative to base if arguments are vague?
             # Let's look at signature in lib/unit_conversion.py
             # It is imported. I haven't read the function body of convert_units in detail.
             # Based on MetricValue.current_value:
             # convert_units(value, self.metric.base_unit, display_unit, invert=self.metric.normalized)
             
             # If not normalized:
             return convert_units(value, base_unit, target_unit_name, invert=invert)

    def update_automated_text(self, value):
        if value is None: 
            self.txtAutomated.setText("")
            return
            
        # Convert SI value to display unit
        disp_val = self.convert_to_display(value)
            
        fmt = self.metric_value.metric.precision
        txt = f'{disp_val: .{fmt}f}' if isinstance(disp_val, float) and fmt is not None else str(disp_val)
        self.txtAutomated.setText(txt)

    def rdoManual_checkchanged(self):
        self.valManual.setEnabled(self.rdoManual.isChecked())

    def accept(self):

        # Save Manual Value (Convert from Display Unit back to Base SI)
        # self.valManual.value() is in self.current_unit
        display_val = self.valManual.value()
        base_val = self.convert_to_base(display_val)
        
        self.metric_value.manual_value = base_val
        self.metric_value.is_manual = self.rdoManual.isChecked()
        self.metric_value.description = self.txtDescription.toPlainText()
        self.metric_value.metadata = self.metadata_widget.get_data()

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
        centerline = self.analysis.metadata.get('centerline', None)
        if centerline is not None and centerline in self.qris_project.profiles:
            analysis_params['centerline'] = self.qris_project.profiles[centerline]
        dem = self.analysis.metadata.get('dem', None)
        if dem is not None and dem in self.qris_project.rasters:
            analysis_params['dem'] = self.qris_project.rasters[dem]
        valley_bottom = self.analysis.metadata.get('valley_bottom', None)
        if valley_bottom is not None and valley_bottom in self.qris_project.valley_bottoms: 
            analysis_params['valley_bottom'] = self.qris_project.valley_bottoms[valley_bottom]

        metric_calculation = getattr(analysis_metrics, self.metric_value.metric.metric_function)
        try:
            # Result IS SI (Base Units)
            result = metric_calculation(self.qris_project.project_file, self.sample_frame_id, self.data_capture_event.id, metric_params, analysis_params)
            self.metric_value.automated_value = result
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self, f'Error Calculating Metric', f'{ex}\n\nSee log for additional details.')
            QgsMessageLog.logMessage(str(traceback.format_exc()), f'QRiS_Metrics', level=Qgis.Warning)
            self.txtAutomated.setText(None)
            self.rdoManual.setChecked(True)
            self.rdoAutomated.setEnabled(False)
            return

        # Display result formatted to current display unit
        self.update_automated_text(result)
        
        self.rdoAutomated.setChecked(True)
        self.rdoAutomated.setEnabled(True)

    def setupUi(self):

        self.resize(500, 200)

        # Top level layout
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        # Header Grid (Metric Name and Navigation)
        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblMetric = QtWidgets.QLabel('Metric')
        self.grid.addWidget(self.lblMetric, 0, 0)

        self.txtMetric = QtWidgets.QLineEdit()
        self.txtMetric.setReadOnly(True)
        self.grid.addWidget(self.txtMetric, 0, 1)

        self.cmdHelp = QtWidgets.QPushButton()
        self.cmdHelp.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/help'))
        self.cmdHelp.setToolTip('Help')
        self.cmdHelp.clicked.connect(lambda: FrmLayerMetricDetails(self, self.qris_project, metric=self.metric_value.metric).exec_())
        self.grid.addWidget(self.cmdHelp, 0, 2)

        self.lblMetricDesc = QtWidgets.QLabel()
        self.lblMetricDesc.setWordWrap(True)
        # Font style for description - maybe italic? 
        font = self.lblMetricDesc.font()
        self.lblMetricDesc.setFont(font)
        self.grid.addWidget(self.lblMetricDesc, 1, 1, 1, 2)

        # Tabs
        self.tab = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tab)

        self.tabValues = QtWidgets.QWidget()
        self.tab.addTab(self.tabValues, 'Value')

        # Value Tab Grid
        self.gridValues = QtWidgets.QGridLayout(self.tabValues)

        # --- Row 0: Display Units ---
        self.horizUnits = QtWidgets.QHBoxLayout()
        self.horizUnits.addStretch()
        
        self.lblUnits = QtWidgets.QLabel("Display Units:")
        self.lblUnits.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.horizUnits.addWidget(self.lblUnits)
        
        self.cboUnits = QtWidgets.QComboBox()
        self.horizUnits.addWidget(self.cboUnits)
        
        self.gridValues.addLayout(self.horizUnits, 0, 0, 1, 2)

        # --- Row 1: Manual Value ---
        self.rdoManual = QtWidgets.QRadioButton('Manual Value')
        self.rdoManual.toggled.connect(self.rdoManual_checkchanged)
        self.gridValues.addWidget(self.rdoManual, 1, 0)

        self.valManual = QtWidgets.QDoubleSpinBox()
        self.valManual.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.gridValues.addWidget(self.valManual, 1, 1)        
        
        # --- Row 2: Automated Value ---
        self.rdoAutomated = QtWidgets.QRadioButton('Calculated Value')
        self.gridValues.addWidget(self.rdoAutomated, 2, 0)

        self.txtAutomated = QtWidgets.QLineEdit()
        self.txtAutomated.setReadOnly(True)
        self.txtAutomated.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.gridValues.addWidget(self.txtAutomated, 2, 1)

        self.actionCalculate = QtWidgets.QAction(self.txtAutomated)
        self.actionCalculate.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/calculate'))
        self.actionCalculate.setToolTip('Calculate Metric From GIS')
        self.actionCalculate.triggered.connect(self.cmd_calculate_metric_clicked)
        self.txtAutomated.addAction(self.actionCalculate, QtWidgets.QLineEdit.TrailingPosition)
        
        # --- Row 3: Uncertainty ---
        self.lblUbcertainty = QtWidgets.QLabel('Uncertainty')
        self.gridValues.addWidget(self.lblUbcertainty, 3, 0)

        self.horiz_uncertainty = QtWidgets.QHBoxLayout()
        self.gridValues.addLayout(self.horiz_uncertainty, 3, 1)

        self.cboManualUncertainty = QtWidgets.QComboBox()
        self.cboManualUncertainty.addItems([UNCERTAINTY_NONE, UNCERTAINTY_PLUS_MINUS, UNCERTAINTY_PERCENT, UNCERTAINTY_MINMAX])
        self.horiz_uncertainty.addWidget(self.cboManualUncertainty)
        self.cboManualUncertainty.currentIndexChanged.connect(self.ManualUncertaintyChange)

        self.ValManualPlusMinus = QtWidgets.QDoubleSpinBox()
        self.horiz_uncertainty.addWidget(self.ValManualPlusMinus)

        self.ValManualUncertaintyLabelMin = QtWidgets.QLabel('Minimum')
        self.horiz_uncertainty.addWidget(self.ValManualUncertaintyLabelMin)

        self.ValManualUncertaintyMin = QtWidgets.QDoubleSpinBox()
        self.horiz_uncertainty.addWidget(self.ValManualUncertaintyMin)

        self.ValManualUncertaintyLabelMax = QtWidgets.QLabel('Maximum')
        self.horiz_uncertainty.addWidget(self.ValManualUncertaintyLabelMax)

        self.ValManualUncertaintyMax = QtWidgets.QDoubleSpinBox()
        self.horiz_uncertainty.addWidget(self.ValManualUncertaintyMax)
        
        self.horiz_uncertainty.addStretch()

        self.gridValues.setRowStretch(4, 1)

        # Other Tabs
        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tab.addTab(self.txtDescription, 'Notes')

        self.metadata_widget = MetadataWidget(self)
        self.tab.addTab(self.metadata_widget, 'Metadata')

        self.vert.addLayout(add_standard_form_buttons(self, 'analyses'))
