import sqlite3
import json

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QFileDialog, QPushButton, QRadioButton, QVBoxLayout, QHBoxLayout, QGridLayout, QDialogButtonBox, QLabel, QTabWidget, QTableWidget, QTableWidgetItem

from ..model.project import Project
from ..model.metric import METRIC_SCHEMA, insert_metric

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

            headers = ['', 'Name', 'Machine Name', 'Calculation', 'Default Level', 'Units', 'Description', 'Definition URL', 'Metadata', "Metric Params", ""]
            self.metrics_table.setRowCount(len(self.qris_project.metrics))
            self.metrics_table.setColumnCount(len(headers))
            self.metrics_table.setHorizontalHeaderLabels(headers)
            self.metrics_table.verticalHeader().hide()

            for i, metric in enumerate(self.qris_project.metrics.values()):
                metadata = json.dumps(metric.metadata) if metric.metadata is not None else ''
                metric_params = json.dumps(metric.metric_params) if metric.metric_params is not None else ''
                
                # add an exprot metric button
                export_button = QPushButton("Export")
                export_button.setStyleSheet("padding: 3px;") 
                export_button.clicked.connect(lambda _, i=i: self.export_metric(i))
                self.metrics_table.setCellWidget(i, 0, export_button)
                self.metrics_table.setItem(i, 1, QTableWidgetItem(metric.name))
                self.metrics_table.setItem(i, 2, QTableWidgetItem(metric.machine_name))
                self.metrics_table.setItem(i, 3, QTableWidgetItem(metric.metric_function))
                self.metrics_table.setItem(i, 4, QTableWidgetItem(self.levels.get(metric.default_level_id, None)))
                self.metrics_table.setItem(i, 5, QTableWidgetItem(self.units.get(metric.default_unit_id, None if metric.default_unit_id is not None else None)))
                self.metrics_table.setItem(i, 6, QTableWidgetItem(metric.description))
                self.metrics_table.setItem(i, 7, QTableWidgetItem(metric.definition_url))
                self.metrics_table.setItem(i, 8, QTableWidgetItem(metadata))
                self.metrics_table.setItem(i, 9, QTableWidgetItem(metric_params))
                delete_button = QPushButton()
                delete_button.setIcon(QIcon(':/plugins/qris_toolbar/delete'))
                delete_button.setStyleSheet("padding: 0px;") 
                delete_button.clicked.connect(lambda _, i=i: self.delete_metric(i))
                self.metrics_table.setCellWidget(i, 10, delete_button)

            # Set the column widths to fit the contents of cells with buttons
            self.metrics_table.resizeColumnsToContents()
            for i in range(self.metrics_table.columnCount()):
                if self.metrics_table.columnWidth(i) > 250:
                    self.metrics_table.setColumnWidth(i, 250)
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
            
            self.metrics_save_button.setEnabled(False)
            self.metrics_import_button.setEnabled(False)

    def import_metrics(self):
        import_file = QFileDialog.getOpenFileName(self, "Import Metrics File", "", "JSON Files (*.json)")
        if import_file[0]:
            with open(import_file[0], 'r') as file:
                metric = json.load(file)

                for i in range(self.metrics_table.rowCount()):
                    if self.metrics_table.item(i, 2).text() == metric['machine_name']:
                        QMessageBox.warning(self, "Import Metric", f"Metric {metric['machine_name']} already exists.")
                        return
                        # TODO - add overwrite option. this will impact the database and/or existing metrics in the project 
                        # # user can decide to overwrite the metric
                        # reply = QMessageBox.question(self, "Import Metric", f"Metric {metric['machine_name']} already exists. Overwrite?", QMessageBox.Yes | QMessageBox.No)
                        # if reply == QMessageBox.No:
                        #     return

                self.metrics_table.setRowCount(self.metrics_table.rowCount() + 1)
                row = self.metrics_table.rowCount() - 1

                # add an exprot metric button
                export_button = QPushButton("Export")
                export_button.setStyleSheet("padding: 3px;")
                export_button.clicked.connect(lambda _, i=row: self.export_metric(i))
                self.metrics_table.setCellWidget(row, 0, export_button)
                self.metrics_table.setItem(row, 1, QTableWidgetItem(metric['name']))
                self.metrics_table.setItem(row, 2, QTableWidgetItem(metric['machine_name']))
                self.metrics_table.setItem(row, 3, QTableWidgetItem(metric['calculation_name']))
                self.metrics_table.setItem(row, 4, QTableWidgetItem(metric['default_level']))
                self.metrics_table.setItem(row, 5, QTableWidgetItem(metric['units']))
                self.metrics_table.setItem(row, 6, QTableWidgetItem(metric['description']))
                self.metrics_table.setItem(row, 7, QTableWidgetItem(metric['definition_url']))
                self.metrics_table.setItem(row, 8, QTableWidgetItem(json.dumps(metric['metadata'])))
                self.metrics_table.setItem(row, 9, QTableWidgetItem(json.dumps(metric['metric_params'])))
                delete_button = QPushButton()
                delete_button.setIcon(QIcon(':/plugins/qris_toolbar/delete'))
                delete_button.clicked.connect(lambda _, i=row: self.delete_metric(i))
                self.metrics_table.setCellWidget(row, 10, delete_button)

        if self.metrics_table.rowCount() == 1:
            self.metrics_table.resizeColumnsToContents()
            for i in range(self.metrics_table.columnCount()):
                if self.metrics_table.columnWidth(i) > 250:
                    self.metrics_table.setColumnWidth(i, 250)

    def delete_metric(self, index_row):

        metric_name = self.metrics_table.item(index_row, 1).text()
        metric_machine_name = self.metrics_table.item(index_row, 2).text()

        # User warning
        reply = QMessageBox.question(self, "Delete Metric", f"Are you sure you want to delete metric {metric_name}?\nAll calculated metric values associated with this metric will be also be deleted. Changes will be applied to the project immediately.", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        self.metrics_table.removeRow(index_row)

        # if the metric is in the project, remove it
        for metric_id, metric in self.qris_project.metrics.items():
            if metric.machine_name == metric_machine_name:
                # now remove it from the database
                try:
                    with sqlite3.connect(self.qris_project.project_file) as conn:
                        curs = conn.cursor()
                        curs.execute('DELETE FROM metric_values WHERE metric_id = ?', [metric_id])
                        curs.execute('DELETE FROM analysis_metrics WHERE metric_id = ?', [metric_id])
                        curs.execute('DELETE FROM metrics WHERE machine_name = ?', [metric_machine_name])
                    del self.qris_project.metrics[metric_id]
                    # loop through the analyses and remove the metric from the analysis metrics
                    for analysis in self.qris_project.analyses.values():
                        if metric_id in analysis.analysis_metrics:
                            del analysis.analysis_metrics[metric_id]
                    conn.commit()
                except Exception as e:
                    QMessageBox.warning(self, "Delete Metric", f"Error deleting metric {metric_name}: {str(e)}")
                    conn.rollback()
                break
                
    def export_metric(self, index_row):

        initial_file = self.metrics_table.item(index_row, 2).text()
        export_file = QFileDialog.getSaveFileName(self, "Export Metrics File", initial_file, "JSON Files (*.json)")

        if export_file[0]:

            i = index_row

            out_metric = {
                '$schema': METRIC_SCHEMA,
                'name': self.metrics_table.item(i, 1).text(),
                'machine_name': self.metrics_table.item(i, 2).text(),
                'calculation_name': self.metrics_table.item(i, 3).text(),
                'default_level': self.metrics_table.item(i, 4).text(),
                'units': self.metrics_table.item(i, 5).text() if self.metrics_table.item(i, 5).text() != '' else None,
                'description': self.metrics_table.item(i, 6).text() if self.metrics_table.item(i, 6).text() != '' else None,
                'definition_url': self.metrics_table.item(i, 7).text() if self.metrics_table.item(i, 7).text() != '' else None,
                'metadata': json.loads(self.metrics_table.item(i, 8).text()),
                'metric_params': json.loads(self.metrics_table.item(i, 9).text())
            }

            with open(export_file[0], 'w') as file:
                json.dump(out_metric, file, indent=4)

            # successful export message in message box
            QMessageBox.information(self, "Export Metrics", f"Metrics exported successfully to {export_file[0]}")

    def save_metrics(self):

        saved_metrics = 0
        # lets add any new metrics in the table to the project
        for i in range(self.metrics_table.rowCount()):
            name = self.metrics_table.item(i, 1).text()
            machine_name = self.metrics_table.item(i, 2).text()
            description = self.metrics_table.item(i, 6).text()
            metric_function = self.metrics_table.item(i, 3).text()
            metric_params = json.loads(self.metrics_table.item(i, 9).text())
            metadata = json.loads(self.metrics_table.item(i, 8).text())
            default_level = self.metrics_table.item(i, 4).text()
            default_unit = self.metrics_table.item(i, 5).text()
            definition_url = self.metrics_table.item(i, 7).text()

            if all(name != metric.name for metric in self.qris_project.metrics.values()):
                metric_id, metric = insert_metric(self.qris_project.project_file, name, machine_name, description, default_level, metric_function, metric_params, default_unit, definition_url, metadata)
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

        self.vertGeneral = QVBoxLayout()
        self.grid = QGridLayout()

        self.label = QLabel("Default Dock widget location")
        self.grid.addWidget(self.label, 0, 0, 1, 2)

        self.left_radio = QRadioButton("Dock to left")
        self.right_radio = QRadioButton("Dock to right")
        self.grid.addWidget(self.left_radio, 1, 0)
        self.grid.addWidget(self.right_radio, 1, 1)

        # add a label to the layout to explain settings will take effect after restarting qgis
        self.grid.addWidget(QLabel("Settings will take effect after restarting QGIS"))

        self.vertGeneral.addLayout(self.grid)
        self.vertGeneral.addStretch(1)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.vert.addWidget(self.button_box)

        self.tabSettings = QWidget()
        self.tabs.addTab(self.tabSettings, "General")
        self.tabSettings.setLayout(self.vertGeneral)

        self.metrics_layout = QVBoxLayout()
        self.metrics_button_hlayout = QHBoxLayout()
        self.metrics_button_layout = QVBoxLayout()

        # lets add a table widget to display the metrics
        self.metrics_table = QTableWidget()
        self.metrics_layout.addWidget(self.metrics_table)

        # add buttons for importing and exporting metrics to json
        self.metrics_import_button = QPushButton("Import Metrics File")
        self.metrics_import_button.clicked.connect(self.import_metrics)
        self.metrics_button_layout.addWidget(self.metrics_import_button)

        self.metrics_save_button = QPushButton("Save Metrics")
        self.metrics_save_button.clicked.connect(self.save_metrics)
        self.metrics_button_layout.addWidget(self.metrics_save_button)

        self.metrics_button_hlayout.addStretch(1)
        self.metrics_button_hlayout.addLayout(self.metrics_button_layout)

        self.metrics_layout.addLayout(self.metrics_button_hlayout)

        self.tabMetrics = QWidget()
        self.tabs.addTab(self.tabMetrics, "Metrics")
        self.tabMetrics.setLayout(self.metrics_layout)
