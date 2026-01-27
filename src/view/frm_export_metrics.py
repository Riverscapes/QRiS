import json
import xlwt

from PyQt5 import QtWidgets
from qgis.utils import Qgis
from qgis.gui import QgisInterface

from ..model.sample_frame import get_sample_frame_ids
from ..model.metric_value import MetricValue, load_metric_values
from ..model.analysis import Analysis
from ..model.project import Project
from ..model.metric import Metric
from ..lib.unit_conversion import short_unit_name

from .utilities import add_standard_form_buttons


class FrmExportMetrics(QtWidgets.QDialog):

    def __init__(self, parent, iface: QgisInterface, project: Project, analysis: Analysis=None, current_dce=None, current_sf=None):
        super().__init__(parent)

        self.iface = iface
        self.project = project
        self.analysis = analysis
        self.current_dce = current_dce
        self.current_sf = current_sf

        if self.analysis is not None:
            self.analyses = {analysis: get_sample_frame_ids(self.project.project_file, self.analysis.sample_frame.id)}
        else:
            self.analyses = {analysis: get_sample_frame_ids(self.project.project_file, analysis.sample_frame.id) for analysis in self.project.analyses.values()}

        self.setWindowTitle("Export Metrics Table")
        self.setupUi()

        if self.current_dce is None:
            self.rdoAllDCE.setChecked(True)
            # hide the groupbox for DCEs
            self.grpDCE.setEnabled(False)
            self.grpDCE.setVisible(False)

        if self.current_sf is None:
            self.rdoAllSF.setChecked(True)
            # hide the groupbox for SFs
            self.grpSF.setEnabled(False)
            self.grpSF.setVisible(False)

    def browse_path(self):

        output_format = self.combo_format.currentText()
        output_ext = "xls" if output_format == "Excel" else output_format.lower()

        path = QtWidgets.QFileDialog.getSaveFileName(self, "Export Metrics Table", "", f"{output_format} Files (*.{output_ext})")[0]
        self.txtOutpath.setText(path)

    def format_change(self):

        # if the edit_location is not empty, then change the extension to match the new format
        if self.txtOutpath.text() != "":
            path = self.txtOutpath.text()
            output_format = self.combo_format.currentText()
            if output_format == "Excel":
                output_format = "xls"
            path = path[:path.rfind(".") + 1] + output_format.lower()
            self.txtOutpath.setText(path)

    def accept(self) -> None:

        if not self.txtOutpath.text():
            QtWidgets.QMessageBox.warning(self, "Export Metrics Table", "Please specify an output file.")
            return

        # try:
        out_values = []

        data_capture_events = list(self.project.events.values()) if self.rdoAllDCE.isChecked() else [self.current_dce]
        for analysis, sample_frame_ids in self.analyses.items():
            sample_frame_features = list(sample_frame_ids.values()) if self.rdoAllSF.isChecked() else [self.current_sf]
            for sample_frame_feature in sample_frame_features:
                for data_capture_event in data_capture_events:
                    metric_values = load_metric_values(
                        self.project.project_file,
                        analysis,
                        data_capture_event,
                        sample_frame_feature.id,
                        self.project.metrics
                    )
                    values = {
                        'analysis_name': analysis.name,
                        'sample_frame_id': sample_frame_feature.id,
                        'data_capture_event_id': data_capture_event.id,
                        'sample_frame_feature_name': sample_frame_feature.name,
                        'data_capture_event_name': data_capture_event.name
                    }
                    for analysis_metric in analysis.analysis_metrics.values():
                        metric: Metric = analysis_metric.metric

                        # --- Consistent display unit logic ---
                        display_unit = analysis.units.get(metric.unit_type, None)
                        if metric.normalized and display_unit not in [None, 'ratio', 'count']:
                            display_unit = analysis.units['distance']
                        display_unit_for_value = None if display_unit in ['count', 'ratio'] else display_unit

                        # --- Header logic: always use metric.unit_type for numerator ---
                        # Get the actual unit string for numerator
                        unit_str_raw = analysis.units.get(metric.unit_type, None)
                        numerator = short_unit_name(unit_str_raw) if unit_str_raw not in [None, 'count', 'ratio', 'percent'] else (
                            '#' if unit_str_raw == 'count' else
                            '%' if unit_str_raw == 'percent' else
                            '')

                        # For normalized metrics, use the actual normalization unit string
                        if metric.normalized and unit_str_raw not in [None, 'ratio']:
                            normalization_unit_raw = analysis.units.get('distance', 'm')
                            denominator = short_unit_name(normalization_unit_raw)
                            unit_str = f'{numerator}/{denominator}' if numerator else f'/{denominator}'
                        else:
                            unit_str = numerator

                        metric_name = f'{metric.name} ({unit_str})' if unit_str else metric.name

                        metric_value: MetricValue = metric_values.get(
                            metric.id,
                            MetricValue(metric, None, None, False, None, None, metric.default_unit_id, None)
                        )

                        # --- Use current_value_as_string for formatting and conversion ---
                        value = metric_value.manual_value if metric_value.is_manual == 1 else metric_value.current_value_as_string(display_unit_for_value)
                        value = value if value is not None else ''
                        values.update({metric_name: value})
                        
                        if self.chkIncludeUncertainty.isChecked():
                            uncertainty = metric_value.uncertainty_as_string()
                            values.update({f'{metric_name} Uncertainty': uncertainty})
                    out_values.append(values)

        if self.combo_format.currentText() == 'CSV':
            # write csv file
            with open(self.txtOutpath.text(), 'w') as f:
                f.write(','.join(out_values[0].keys()) + '\n')
                for values in out_values:
                    f.write(','.join([str(v) for v in values.values()]) + '\n')
        elif self.combo_format.currentText() == 'JSON':
            # write json file
            with open(self.txtOutpath.text(), 'w') as f:
                json.dump(out_values, f)
        elif self.combo_format.currentText() == 'Excel':
            # write to excel file
            # create workbook
            wb = xlwt.Workbook()
            # create worksheet
            ws = wb.add_sheet('Metrics')
            # write header row
            for col, key in enumerate(out_values[0].keys()):
                ws.write(0, col, key)
            # write data rows
            for row, values in enumerate(out_values):
                for col, value in enumerate(values.values()):
                    ws.write(row + 1, col, value)
            # save workbook
            wb.save(self.txtOutpath.text())
        else:
            raise Exception("Unsupported output format.")

        # except Exception as ex:
            # QtWidgets.QMessageBox.critical(self, "Export Metrics Table", f"Error exporting metrics table: {ex}")
            # return

        self.iface.messageBar().pushMessage('Export Metrics', f'Exported metrics to {self.txtOutpath.text()}', level=Qgis.Success)
        return super().accept()

    def setupUi(self):

        self.setMinimumSize(500, 300)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        # Groupbox named "Data Capture Events" with radio buttons for "just the currently active DCE" or "All Data Capture Events"
        self.grpDCE = QtWidgets.QGroupBox('Data Capture Events')
        self.rdoActiveDCE = QtWidgets.QRadioButton('Just the currently active Data Capture Event')
        self.rdoActiveDCE.setToolTip('Export metrics for the only currently active Data Capture Event')
        self.rdoAllDCE = QtWidgets.QRadioButton('All Data Capture Events')
        self.rdoAllDCE.setToolTip('Export metrics for all Data Capture Events in the project')
        self.rdoActiveDCE.setChecked(True)
        self.grpDCE.setLayout(QtWidgets.QVBoxLayout())
        self.grpDCE.layout().addWidget(self.rdoActiveDCE)
        self.grpDCE.layout().addWidget(self.rdoAllDCE)
        self.vert.addWidget(self.grpDCE)

        # groupbox named Sampling Frames with radio buttons for "just the currently active SF" or "All Sampling Frames"
        self.grpSF = QtWidgets.QGroupBox('Sample Frames')
        self.rdoActiveSF = QtWidgets.QRadioButton('Just the currently active Sample Frame')
        self.rdoActiveSF.setToolTip('Export metrics for the only currently active Sample Frame')
        self.rdoAllSF = QtWidgets.QRadioButton('All Sample Frames')
        self.rdoAllSF.setToolTip('Export metrics for all Sample Frames in the project')
        self.rdoActiveSF.setChecked(True)
        self.grpSF.setLayout(QtWidgets.QVBoxLayout())
        self.grpSF.layout().addWidget(self.rdoActiveSF)
        self.grpSF.layout().addWidget(self.rdoAllSF)
        self.vert.addWidget(self.grpSF)

        self.export_grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.export_grid)

        # check box for including uncertainty
        self.chkIncludeUncertainty = QtWidgets.QCheckBox("Include Value Uncertainty Columns in Export")
        self.chkIncludeUncertainty.setToolTip("Include the uncertainty value for each metric in the export")
        self.chkIncludeUncertainty.setChecked(False)
        self.export_grid.addWidget(self.chkIncludeUncertainty, 0, 0, 1, 2)

        # label for export format
        self.lbl_format = QtWidgets.QLabel("Export Format")
        self.export_grid.addWidget(self.lbl_format, 1, 0, 1, 1)

        self.horiz_format = QtWidgets.QHBoxLayout()
        self.export_grid.addLayout(self.horiz_format, 1, 1, 1, 1)

        # drop down for export format
        self.combo_format = QtWidgets.QComboBox()
        self.combo_format.setToolTip("Select the format to export the metrics table")
        self.combo_format.addItems(["CSV", "JSON", "Excel"])
        self.combo_format.currentTextChanged.connect(self.format_change)
        self.horiz_format.addWidget(self.combo_format)

        # add spacer
        self.horiz_format.addStretch()

        # label for export location
        self.lbl_location = QtWidgets.QLabel("Export Path")
        self.export_grid.addWidget(self.lbl_location, 2, 0, 1, 1)

        self.horizOutput = QtWidgets.QHBoxLayout()
        self.export_grid.addLayout(self.horizOutput, 2, 1, 1, 1)

        # line edit for export location
        self.txtOutpath = QtWidgets.QLineEdit()
        self.txtOutpath.setToolTip("Specify the location to save the exported metrics table")
        self.txtOutpath.setReadOnly(True)
        self.horizOutput.addWidget(self.txtOutpath)

        # button for export location
        self.btn_location = QtWidgets.QPushButton("...")
        self.btn_location.setToolTip("Browse to the directory to save the exported metrics table")
        self.btn_location.clicked.connect(self.browse_path)
        self.horizOutput.addWidget(self.btn_location)

        # add vertical spacer
        self.vert.addStretch()

        # add standard form buttons
        self.vert.addLayout(add_standard_form_buttons(self, "metrics"))
