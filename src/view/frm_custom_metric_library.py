import json
import re
import sqlite3
from datetime import date
from typing import Optional, Tuple

from qgis.PyQt import QtCore, QtWidgets

from ..model.project import Project
from ..model.analysis import Analysis
from ..model.metric import Metric, insert_metric
from ..model.protocol import Protocol


CUSTOM_PROTOCOL_MACHINE_CODE = 'CUSTOM_METRIC_PROTOCOL'
CUSTOM_PROTOCOL_VERSION = '1.0'
CUSTOM_PROTOCOL_LABEL = 'Custom Metrics'
CUSTOM_PROTOCOL_DESCRIPTION = 'Project-scoped custom manual metrics.'


class CustomMetricCreateDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add Custom Metric')
        self.setMinimumWidth(420)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self.txt_name = QtWidgets.QLineEdit()
        self.txt_name.setPlaceholderText('Metric display name')
        form.addRow('Metric Name', self.txt_name)

        self.cbo_type = QtWidgets.QComboBox()
        self.cbo_type.addItem('Float', 'float')
        self.cbo_type.addItem('Integer', 'int')
        self.cbo_type.currentIndexChanged.connect(self._on_type_changed)
        form.addRow('Type', self.cbo_type)

        self.txt_min = QtWidgets.QLineEdit()
        self.txt_min.setPlaceholderText('Optional')
        form.addRow('Minimum Value', self.txt_min)

        self.txt_max = QtWidgets.QLineEdit()
        self.txt_max.setPlaceholderText('Optional')
        form.addRow('Maximum Value', self.txt_max)

        self.spn_precision = QtWidgets.QSpinBox()
        self.spn_precision.setRange(0, 12)
        self.spn_precision.setValue(2)
        form.addRow('Precision (float only)', self.spn_precision)

        self.txt_tolerance = QtWidgets.QLineEdit()
        self.txt_tolerance.setPlaceholderText('Optional')
        form.addRow('Tolerance', self.txt_tolerance)

        layout.addLayout(form)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept_with_validation)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_type_changed()

    def _on_type_changed(self):
        is_float = self.cbo_type.currentData() == 'float'
        self.spn_precision.setEnabled(is_float)

    def _parse_numeric(self, text: str, is_float: bool) -> Tuple[Optional[float], bool]:
        if text is None:
            return None, True
        raw = text.strip()
        if raw == '':
            return None, True
        try:
            if is_float:
                return float(raw), True
            return int(raw), True
        except ValueError:
            return None, False

    def _accept_with_validation(self):
        name = self.txt_name.text().strip()
        is_float = self.cbo_type.currentData() == 'float'

        if not name:
            QtWidgets.QMessageBox.warning(self, 'Invalid Metric', 'Metric name is required.')
            return

        min_val, ok_min = self._parse_numeric(self.txt_min.text(), is_float)
        max_val, ok_max = self._parse_numeric(self.txt_max.text(), is_float)
        tol_val, ok_tol = self._parse_numeric(self.txt_tolerance.text(), True)

        if not ok_min or not ok_max:
            QtWidgets.QMessageBox.warning(self, 'Invalid Metric', 'Minimum and Maximum must be valid numeric values.')
            return

        if not ok_tol:
            QtWidgets.QMessageBox.warning(self, 'Invalid Metric', 'Tolerance must be a valid numeric value.')
            return

        if min_val is not None and max_val is not None and min_val > max_val:
            QtWidgets.QMessageBox.warning(self, 'Invalid Metric', 'Minimum value cannot be greater than maximum value.')
            return

        self.accept()

    def get_values(self) -> dict:
        is_float = self.cbo_type.currentData() == 'float'
        min_val = self.txt_min.text().strip()
        max_val = self.txt_max.text().strip()
        tol_val = self.txt_tolerance.text().strip()
        return {
            'name': self.txt_name.text().strip(),
            'type': 'float' if is_float else 'int',
            'minimum_value': float(min_val) if is_float and min_val else (int(min_val) if min_val else None),
            'maximum_value': float(max_val) if is_float and max_val else (int(max_val) if max_val else None),
            'precision': self.spn_precision.value() if is_float else None,
            'tolerance': float(tol_val) if tol_val else None,
        }


class FrmCustomMetricLibrary(QtWidgets.QDialog):
    def __init__(self, parent, qris_project: Project, analysis: Analysis = None):
        super().__init__(parent)
        self.qris_project = qris_project
        self.analysis = analysis
        self.changed = False

        self.setWindowTitle('Custom Metric Library')
        self.setMinimumWidth(780)
        self.setMinimumHeight(420)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel('Project-scoped custom manual metrics in Custom Metrics protocol:'))

        self.tbl_metrics = QtWidgets.QTableWidget(0, 7)
        self.tbl_metrics.setHorizontalHeaderLabels([
            'Name', 'Metric ID', 'Type', 'Min', 'Max', 'Precision', 'Tolerance'
        ])
        self.tbl_metrics.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tbl_metrics.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tbl_metrics.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbl_metrics.verticalHeader().setVisible(False)
        header = self.tbl_metrics.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
        layout.addWidget(self.tbl_metrics)

        button_row = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton('Add Metric')
        self.btn_edit = QtWidgets.QPushButton('Edit Name')
        self.btn_delete = QtWidgets.QPushButton('Delete Metric')
        button_row.addWidget(self.btn_add)
        button_row.addWidget(self.btn_edit)
        button_row.addWidget(self.btn_delete)
        button_row.addStretch()
        layout.addLayout(button_row)

        dlg_buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        dlg_buttons.rejected.connect(self.reject)
        dlg_buttons.accepted.connect(self.accept)
        dlg_buttons.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.accept)
        layout.addWidget(dlg_buttons)

        self.btn_add.clicked.connect(self._on_add_metric)
        self.btn_edit.clicked.connect(self._on_edit_name)
        self.btn_delete.clicked.connect(self._on_delete_metric)

        self._refresh_table()

    def _find_custom_protocol(self) -> Optional[Protocol]:
        for protocol in self.qris_project.protocols.values():
            if protocol.machine_code == CUSTOM_PROTOCOL_MACHINE_CODE:
                return protocol
        return None

    def _ensure_custom_protocol(self) -> Protocol:
        existing = self._find_custom_protocol()
        if existing is not None:
            return existing

        created_on = date.today().isoformat()
        metadata = {
            'system': {
                'status': 'active',
                'protocol_type': 'custom',
                'author': 'User',
                'creation_date': created_on,
                'updated_date': created_on,
            }
        }

        with sqlite3.connect(self.qris_project.project_file) as conn:
            curs = conn.cursor()
            curs.execute(
                'INSERT INTO protocols (name, machine_code, has_custom_ui, description, version, metadata) VALUES (?, ?, ?, ?, ?, ?)',
                (CUSTOM_PROTOCOL_LABEL, CUSTOM_PROTOCOL_MACHINE_CODE, False, CUSTOM_PROTOCOL_DESCRIPTION, CUSTOM_PROTOCOL_VERSION, json.dumps(metadata))
            )
            protocol_id = curs.lastrowid

        protocol = Protocol(
            protocol_id,
            CUSTOM_PROTOCOL_LABEL,
            CUSTOM_PROTOCOL_MACHINE_CODE,
            False,
            CUSTOM_PROTOCOL_DESCRIPTION,
            CUSTOM_PROTOCOL_VERSION,
            metadata,
            protocol_layers={},
        )
        self.qris_project.protocols[protocol.id] = protocol
        return protocol

    def _custom_metrics(self):
        metrics = [
            metric for metric in self.qris_project.metrics.values()
            if metric.protocol_machine_code == CUSTOM_PROTOCOL_MACHINE_CODE
        ]
        return sorted(metrics, key=lambda m: (m.machine_name, str(m.version)))

    def _next_metric_machine_name(self) -> str:
        max_idx = 0
        pattern = re.compile(r'^custom_metric_(\d+)$')
        for metric in self._custom_metrics():
            match = pattern.match(metric.machine_name or '')
            if not match:
                continue
            max_idx = max(max_idx, int(match.group(1)))
        return f'custom_metric_{max_idx + 1:03d}'

    def _selected_metric(self) -> Optional[Metric]:
        row = self.tbl_metrics.currentRow()
        if row < 0:
            return None
        item = self.tbl_metrics.item(row, 0)
        if item is None:
            return None
        return item.data(QtCore.Qt.UserRole)

    def _refresh_table(self):
        metrics = self._custom_metrics()
        self.tbl_metrics.setRowCount(len(metrics))

        for row, metric in enumerate(metrics):
            metadata = metric.metadata or {}
            metric_type = metadata.get('custom_metric_type', 'float')
            min_val = metadata.get('minimum_value', '')
            max_val = metadata.get('maximum_value', '')
            precision = metadata.get('precision', '')
            tolerance = metadata.get('tolerance', '')

            name_item = QtWidgets.QTableWidgetItem(metric.name)
            name_item.setData(QtCore.Qt.UserRole, metric)
            self.tbl_metrics.setItem(row, 0, name_item)
            self.tbl_metrics.setItem(row, 1, QtWidgets.QTableWidgetItem(metric.machine_name))
            self.tbl_metrics.setItem(row, 2, QtWidgets.QTableWidgetItem(str(metric_type)))
            self.tbl_metrics.setItem(row, 3, QtWidgets.QTableWidgetItem('' if min_val is None else str(min_val)))
            self.tbl_metrics.setItem(row, 4, QtWidgets.QTableWidgetItem('' if max_val is None else str(max_val)))
            self.tbl_metrics.setItem(row, 5, QtWidgets.QTableWidgetItem('' if precision is None else str(precision)))
            self.tbl_metrics.setItem(row, 6, QtWidgets.QTableWidgetItem('' if tolerance is None else str(tolerance)))

    def _on_add_metric(self):
        protocol = self._ensure_custom_protocol()
        dlg = CustomMetricCreateDialog(self)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        values = dlg.get_values()
        machine_name = self._next_metric_machine_name()
        metadata = {
            'custom_metric_type': values['type'],
            'minimum_value': values['minimum_value'],
            'maximum_value': values['maximum_value'],
            'precision': values['precision'],
            'tolerance': values['tolerance'],
            'status': 'active',
            'hierarchy': ['Custom Metrics'],
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}

        metric_id, metric_obj = insert_metric(
            self.qris_project.project_file,
            values['name'],
            machine_name,
            protocol.machine_code,
            'User-defined custom manual metric',
            'Metric',
            'manual',
            None,
            None,
            None,
            metadata,
            '1.0',
        )
        self.qris_project.metrics[metric_id] = metric_obj
        self.changed = True
        self._refresh_table()

    def _on_edit_name(self):
        metric = self._selected_metric()
        if metric is None:
            QtWidgets.QMessageBox.information(self, 'Edit Name', 'Select a custom metric first.')
            return

        new_name, ok = QtWidgets.QInputDialog.getText(self, 'Edit Metric Name', 'Display Name', text=metric.name)
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name:
            QtWidgets.QMessageBox.warning(self, 'Edit Name', 'Display name cannot be empty.')
            return

        with sqlite3.connect(self.qris_project.project_file) as conn:
            curs = conn.cursor()
            curs.execute('UPDATE metrics SET name = ? WHERE id = ?', (new_name, metric.id))

        metric.name = new_name
        self.changed = True
        self._refresh_table()

    def _on_delete_metric(self):
        metric = self._selected_metric()
        if metric is None:
            QtWidgets.QMessageBox.information(self, 'Delete Metric', 'Select a custom metric first.')
            return

        result = QtWidgets.QMessageBox.question(
            self,
            'Delete Metric',
            f"Delete custom metric '{metric.name}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if result != QtWidgets.QMessageBox.Yes:
            return

        with sqlite3.connect(self.qris_project.project_file) as conn:
            curs = conn.cursor()
            curs.execute('DELETE FROM analysis_metrics WHERE metric_id = ?', (metric.id,))
            curs.execute('DELETE FROM metrics WHERE id = ?', (metric.id,))

        if metric.id in self.qris_project.metrics:
            del self.qris_project.metrics[metric.id]

        if self.analysis is not None and metric.id in self.analysis.analysis_metrics:
            del self.analysis.analysis_metrics[metric.id]

        self.changed = True
        self._refresh_table()
