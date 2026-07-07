from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QPushButton, QLabel, QComboBox,
                              QMenu, QApplication, QSizePolicy)
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsUnitTypes

from ...lib.unit_conversion import distance_units, area_units, short_unit_name
from ..frm_export_table import FrmTableExport


_AREA_KEYS = {'total_area', 'average_area', 'min_area', 'max_area'}
_LENGTH_KEYS = {'total_length', 'average_length', 'min_length', 'max_length'}

STAT_LABELS = {
    'feature_count': 'Feature Count',
    'total_area': 'Total Area',
    'average_area': 'Average Area',
    'min_area': 'Min Area',
    'max_area': 'Max Area',
    'total_length': 'Total Length',
    'average_length': 'Average Length',
    'min_length': 'Min Length',
    'max_length': 'Max Length',
    'sinuosity': 'Planform Sinuosity',
}


class StatsWidget(QWidget):

    def __init__(self, db_item=None, db_path: str = None, parent=None):
        super().__init__(parent)

        self._db_item = db_item
        self._db_path = db_path
        self._stats_calculated = False
        self._raw_stats = {}
        self._tab_widget = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(['Statistic', 'Value'])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.horizontalHeader().setMinimumSectionSize(80)
        self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stats_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.stats_table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.stats_table)

        # Bottom toolbar: [Refresh] [Units: label] [combo] [stretch] [Export]
        bottom = QHBoxLayout()
        layout.addLayout(bottom)

        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.refresh_stats)
        self.refresh_button.setVisible(False)
        bottom.addWidget(self.refresh_button)

        self.lblUnits = QLabel('Units:')
        self.lblUnits.setVisible(False)
        bottom.addWidget(self.lblUnits)

        self.cboUnits = QComboBox()
        self.cboUnits.setVisible(False)
        self.cboUnits.setMinimumWidth(160)
        self.cboUnits.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cboUnits.currentTextChanged.connect(self._on_unit_changed)
        bottom.addWidget(self.cboUnits)

        bottom.addStretch()

        self.export_button = QPushButton('Export')
        self.export_button.clicked.connect(self._export_table)
        bottom.addWidget(self.export_button)

    def load_from_dict(self, stats: dict):
        """Pre-populate with externally computed stats (e.g. before the record is saved)."""
        self._raw_stats = stats
        self._setup_units_combo(stats)
        self._populate_table(stats)
        self._stats_calculated = True
        self.refresh_button.setVisible(False)

    def add_stats_tab(self, tab_widget, label='Geometry'):
        """Add this widget as a tab only if a db_item exists or pre-loaded stats are present."""
        if self._db_item is None and not self._raw_stats:
            self.hide()
            return
        self._tab_widget = tab_widget
        tab_widget.addTab(self, label)
        tab_widget.currentChanged.connect(self._on_parent_tab_changed)

    def _on_parent_tab_changed(self, index):
        if self._tab_widget and self._tab_widget.tabText(index) == 'Geometry':
            self.load_stats()

    def set_db_item(self, db_item, db_path: str):
        """Update the spatial item and path (e.g. after saving a new record)."""
        self._db_item = db_item
        self._db_path = db_path
        self._stats_calculated = False

    def load_stats(self):
        """Calculate and display stats only if not already done."""
        if not self._stats_calculated:
            self.refresh_stats()

    def refresh_stats(self):
        """Force recalculate and display stats."""
        if self._db_item is None:
            self._show_message('Save the record first to view statistics.')
            return
        try:
            self._raw_stats = self._db_item.get_spatial_stats(self._db_path)
            self._setup_units_combo(self._raw_stats)
            self._populate_table(self._raw_stats)
            self._stats_calculated = True
        except Exception as ex:
            self._show_message(f'Error calculating statistics: {ex}')

    def _setup_units_combo(self, stats: dict):
        keys = set(stats.keys())
        has_area = bool(keys & _AREA_KEYS)
        has_length = bool(keys & _LENGTH_KEYS)

        self.cboUnits.blockSignals(True)
        self.cboUnits.clear()
        if has_area:
            self.cboUnits.addItems(list(area_units.keys()))
            self.cboUnits.setCurrentText(QgsUnitTypes.toString(QgsUnitTypes.AreaSquareMeters))
            self.lblUnits.setVisible(True)
            self.cboUnits.setVisible(True)
        elif has_length:
            self.cboUnits.addItems(list(distance_units.keys()))
            self.cboUnits.setCurrentText(QgsUnitTypes.toString(QgsUnitTypes.DistanceMeters))
            self.lblUnits.setVisible(True)
            self.cboUnits.setVisible(True)
        else:
            self.lblUnits.setVisible(False)
            self.cboUnits.setVisible(False)
        self.cboUnits.blockSignals(False)

    def _on_unit_changed(self, _unit_text):
        if self._raw_stats:
            self._populate_table(self._raw_stats)

    def _convert_value(self, key, value):
        """Returns (converted_value, unit_abbrev) from base units (m or m²)."""
        unit_text = self.cboUnits.currentText()
        if key in _AREA_KEYS and unit_text in area_units:
            factor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.AreaSquareMeters, area_units[unit_text])
            return value * factor, short_unit_name(unit_text)
        if key in _LENGTH_KEYS and unit_text in distance_units:
            factor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMeters, distance_units[unit_text])
            return value * factor, short_unit_name(unit_text)
        return value, ''

    def _show_message(self, message: str):
        self.stats_table.clearSpans()
        self.stats_table.setRowCount(1)
        self.stats_table.setSpan(0, 0, 1, 2)
        self.stats_table.setItem(0, 0, QTableWidgetItem(message))

    _MULTI_ONLY_KEYS = {'average_area', 'min_area', 'max_area', 'average_length', 'min_length', 'max_length'}

    def _populate_table(self, stats: dict):
        single_feature = stats.get('feature_count', 0) == 1
        visible = {k: v for k, v in stats.items() if not (single_feature and k in self._MULTI_ONLY_KEYS)}
        self.stats_table.clearSpans()
        self.stats_table.setRowCount(len(visible))
        for row, (key, value) in enumerate(visible.items()):
            label = STAT_LABELS.get(key, key.replace('_', ' ').title())
            if isinstance(value, float):
                converted, abbrev = self._convert_value(key, value)
                numeric_str = f'{converted:,.2f}'
                display_str = f'{numeric_str} {abbrev}'.strip()
            elif isinstance(value, int):
                numeric_str = str(value)
                display_str = numeric_str
                abbrev = ''
            else:
                numeric_str = str(value) if value is not None else 'N/A'
                display_str = numeric_str
                abbrev = ''
            label_item = QTableWidgetItem(label)
            value_item = QTableWidgetItem(display_str)
            # store numeric-only string for copy actions
            value_item.setData(Qt.UserRole, numeric_str)
            value_item.setData(Qt.UserRole + 1, abbrev)
            self.stats_table.setItem(row, 0, label_item)
            self.stats_table.setItem(row, 1, value_item)
        self.stats_table.resizeColumnToContents(0)

    def _show_context_menu(self, pos):
        item = self.stats_table.itemAt(pos)
        if item is None:
            return
        row = item.row()
        value_item = self.stats_table.item(row, 1)
        if value_item is None:
            return
        numeric_str = value_item.data(Qt.UserRole) or value_item.text()
        full_str = value_item.text()

        menu = QMenu(self)
        copy_value = menu.addAction('Copy Value')
        copy_with_units = menu.addAction('Copy Value with Units')
        action = menu.exec_(self.stats_table.viewport().mapToGlobal(pos))
        if action == copy_value:
            QApplication.clipboard().setText(numeric_str)
        elif action == copy_with_units:
            QApplication.clipboard().setText(full_str)

    def _export_table(self):
        data = []
        for row in range(self.stats_table.rowCount()):
            label_item = self.stats_table.item(row, 0)
            value_item = self.stats_table.item(row, 1)
            if label_item is not None and value_item is not None:
                data.append({'Statistic': label_item.text(), 'Value': value_item.text()})
        name = getattr(self._db_item, 'name', 'statistics') if self._db_item else 'statistics'
        db_path = self._db_path
        frm = FrmTableExport(self, data=data, base_name=f'{name}_stats', project_path=db_path)
        frm.exec_()