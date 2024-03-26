import sqlite3
import json

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QFileDialog, QPushButton, QRadioButton, QVBoxLayout, QGridLayout, QDialogButtonBox, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QSpacerItem

from ..model.project import Project
from ..model.metric import insert_metric

class FrmSettings(QDialog):
    def __init__(self, settings: QSettings, dock_widget_location: str, default_dock_widget_location:str, qris_project: Project):
        super().__init__()

        self.settings = settings
        self.dock_widget_location = dock_widget_location
        self.default_dock_widget_location = default_dock_widget_location
        self.qris_project = qris_project
        self.levels = {}
        self.units = {}

        self.setWindowTitle("QRiS Settings")
        self.setup_ui()

        # Get the dockwidget location from the settings
        dock_location = settings.value(self.dock_widget_location, self.default_dock_widget_location)

        if dock_location == 'left':
            self.left_radio.setChecked(True)
        else:
            self.right_radio.setChecked(True)

        self.load_metrics()

    def accept(self):


        if self.left_radio.isChecked():
            self.settings.setValue(self.dock_widget_location, 'left')
        else:
            self.settings.setValue(self.dock_widget_location, 'right')

        super().accept()

    def load_metrics(self):

        if self.qris_project is not None:

            with sqlite3.connect(self.qris_project.project_file) as conn:
                # get dictionaries of level and unit names
                curs = conn.cursor()
                curs.execute('SELECT id, name FROM metric_levels')
                self.levels = {row[0]: row[1] for row in curs.fetchall()}
                curs.execute('SELECT id, name FROM lkp_units') 
                self.units = {row[0]: row[1] for row in curs.fetchall()}

            headers = ['Name', 'Calculation', 'Default Level', 'Units', 'Description', 'Definition URL', 'Metadata', "Metric Params"]
            self.metrics_table.setRowCount(len(self.qris_project.metrics))
            self.metrics_table.setColumnCount(len(headers))
            self.metrics_table.setHorizontalHeaderLabels(headers)

            for i, metric in enumerate(self.qris_project.metrics.values()):
                metadata = json.dumps(metric.metadata) if metric.metadata is not None else ''
                metric_params = json.dumps(metric.metric_params) if metric.metric_params is not None else ''
                self.metrics_table.setItem(i, 0, QTableWidgetItem(metric.name))
                self.metrics_table.setItem(i, 1, QTableWidgetItem(metric.metric_function))
                self.metrics_table.setItem(i, 2, QTableWidgetItem(self.levels.get(metric.default_level_id, None)))
                self.metrics_table.setItem(i, 3, QTableWidgetItem(self.units.get(metric.default_unit_id, None if metric.default_unit_id is not None else None)))
                self.metrics_table.setItem(i, 4, QTableWidgetItem(metric.description))
                self.metrics_table.setItem(i, 5, QTableWidgetItem(metric.definition_url))
                self.metrics_table.setItem(i, 6, QTableWidgetItem(metadata))
                self.metrics_table.setItem(i, 7, QTableWidgetItem(metric_params))
        else:             
            self.metrics_table.setRowCount(1)
            self.metrics_table.setColumnCount(1)
            # hide column headers
            self.metrics_table.horizontalHeader().hide()
            # hide row headers
            self.metrics_table.verticalHeader().hide()
            self.metrics_table.setItem(0, 0, QTableWidgetItem("No project loaded. Load a project to view metrics."))
            # stretch the row to fill the table
            self.metrics_table.horizontalHeader().setSectionResizeMode(0, 1)

    def import_metrics(self):
        import_file = QFileDialog.getOpenFileName(self, "Import Metrics File", "", "JSON Files (*.json)")
        if import_file[0]:
            with open(import_file[0], 'r') as file:
                metrics = json.load(file)

            for metric in metrics:
                # first check if the metric is already in the table
                for i in range(self.metrics_table.rowCount()):
                    if self.metrics_table.item(i, 0).text() == metric['name']:
                        continue
                        
                self.metrics_table.setRowCount(self.metrics_table.rowCount() + 1)
                row = self.metrics_table.rowCount() - 1

                self.metrics_table.setItem(row, 0, QTableWidgetItem(metric['name']))
                self.metrics_table.setItem(row, 1, QTableWidgetItem(metric['calculation_name']))
                self.metrics_table.setItem(row, 2, QTableWidgetItem(metric['default_level']))
                self.metrics_table.setItem(row, 3, QTableWidgetItem(metric['units']))
                self.metrics_table.setItem(row, 4, QTableWidgetItem(metric['description']))
                self.metrics_table.setItem(row, 5, QTableWidgetItem(metric['definition_url']))
                self.metrics_table.setItem(row, 6, QTableWidgetItem(json.dumps(metric['metadata'])))
                self.metrics_table.setItem(row, 7, QTableWidgetItem(json.dumps(metric['metric_params'])))
                
    def export_metrics(self):
        export_file = QFileDialog.getSaveFileName(self, "Export Metrics File", "", "JSON Files (*.json)")

        if export_file[0]:

            out_metrics = []
            # lets export whats in the table
            for i in range(self.metrics_table.rowCount()):

                out_metrics.append({
                    'name': self.metrics_table.item(i, 0).text(),
                    'calculation_name': self.metrics_table.item(i, 1).text(),
                    'default_level': self.metrics_table.item(i, 2).text(),
                    'units': self.metrics_table.item(i, 3).text(),
                    'description': self.metrics_table.item(i, 4).text(),
                    'definition_url': self.metrics_table.item(i, 5).text(),
                    'metadata': json.loads(self.metrics_table.item(i, 6).text()),
                    'metric_params': json.loads(self.metrics_table.item(i, 7).text())
                })

            with open(export_file[0], 'w') as file:
                json.dump(out_metrics, file, indent=4)

            # successful export message in message box
            QMessageBox.information(self, "Export Metrics", f"Metrics exported successfully to {export_file[0]}")

    def save_metrics(self):

        saved_metrics = 0
        # lets add any new metrics in the table to the project
        for i in range(self.metrics_table.rowCount()):
            name = self.metrics_table.item(i, 0).text()
            default_level = self.metrics_table.item(i, 2).text()
            description = self.metrics_table.item(i, 4).text()
            metric_function = self.metrics_table.item(i, 1).text()
            metric_params = json.loads(self.metrics_table.item(i, 7).text())
            metadata = json.loads(self.metrics_table.item(i, 6).text())

            if all(name != metric.name for metric in self.qris_project.metrics.values()):
                metric_id, metric = insert_metric(self.qris_project.project_file, name, description, default_level, metric_function, metric_params, self.metrics_table.item(i, 3).text(), self.metrics_table.item(i, 5).text(), metadata)
                self.qris_project.metrics[metric_id] = metric
                saved_metrics += 1

        if saved_metrics > 0:
            QMessageBox.information(self, "Save Metrics", f"{saved_metrics} metrics saved to project.")
        else:
            QMessageBox.information(self, "Save Metrics", "No new metrics to save.")


    def setup_ui(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

        self.vert = QVBoxLayout(self)
        self.setLayout(self.vert)
        self.tabs = QTabWidget()
        self.vert.addWidget(self.tabs)

        self.grid = QGridLayout()

        self.label = QLabel("Default Dock widget location")
        self.grid.addWidget(self.label, 0, 0, 1, 2)

        self.left_radio = QRadioButton("Dock to left")
        self.right_radio = QRadioButton("Dock to right")
        self.grid.addWidget(self.left_radio, 1, 0)
        self.grid.addWidget(self.right_radio, 1, 1)

        # add a label to the layout to explain settings will take effect after restarting qgis
        self.grid.addWidget(QLabel("Settings will take effect after restarting QGIS"))

        # insert vertical spacer to push everything to the top
        self.grid.addItem(QSpacerItem(1, 1, 1, 1), 2, 0)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.vert.addWidget(self.button_box)

        self.tabSettings = QWidget()
        self.tabs.addTab(self.tabSettings, "General")
        self.tabSettings.setLayout(self.grid)

        self.metrics_layout = QGridLayout()

        # lets add a table widget to display the metrics
        self.metrics_table = QTableWidget()
        self.metrics_layout.addWidget(self.metrics_table)

        # add buttons for importing and exporting metrics to json
        self.metrics_import_button = QPushButton("Import Metrics File")
        self.metrics_import_button.clicked.connect(self.import_metrics)
        self.metrics_layout.addWidget(self.metrics_import_button)

        self.metrics_export_button = QPushButton("Export Metrics File")
        self.metrics_export_button.clicked.connect(self.export_metrics)
        self.metrics_layout.addWidget(self.metrics_export_button)

        self.metrics_save_button = QPushButton("Save Metrics")
        self.metrics_save_button.clicked.connect(self.save_metrics)
        self.metrics_layout.addWidget(self.metrics_save_button)

        self.tabMetrics = QWidget()
        self.tabs.addTab(self.tabMetrics, "Metrics")
        self.tabMetrics.setLayout(self.metrics_layout)
