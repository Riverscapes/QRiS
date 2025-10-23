import sqlite3
import json

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QFileDialog, QPushButton, QRadioButton, QCheckBox, QVBoxLayout, QHBoxLayout, QGridLayout, QDialogButtonBox, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QLineEdit

from ..model.project import Project

from .frm_export_project import DEFAULT_EXPORT_PATH

DOCK_WIDGET_LOCATION = 'dock_widget_location'
REMOVE_LAYERS_ON_CLOSE = 'remove_layers_on_close'

LOCAL_PROTOCOL_FOLDER = 'local_protocol_folder'
SHOW_EXPERIMENTAL_PROTOCOLS = 'show_experimental_protocols'

default_dock_widget_location = 'right'

class FrmSettings(QDialog):
    def __init__(self, settings: QSettings, qris_project: Project):
        super().__init__()

        self.settings = settings
        self.qris_project = qris_project
        self.levels = {}
        self.units = {}

        self.setWindowTitle("QRiS Settings")
        self.setup_ui()

        # Get the dockwidget location from the settings
        dock_location = settings.value(DOCK_WIDGET_LOCATION, default_dock_widget_location)
        self.left_radio.setChecked(dock_location == 'left')
        self.right_radio.setChecked(dock_location == 'right')

        # Get the remove layers on close setting
        remove_layers_on_close = settings.value(REMOVE_LAYERS_ON_CLOSE, False, type=bool)
        self.chk_remove_layers_on_close.setChecked(remove_layers_on_close)

        # Get the default export path
        default_export_path = settings.value(DEFAULT_EXPORT_PATH, '')
        self.txt_path_export.setText(default_export_path)

        # Get the local protocol folder
        protocol_folder = settings.value(LOCAL_PROTOCOL_FOLDER, '')
        self.txt_protocol_folder.setText(protocol_folder)

        show_experimental_protocols = settings.value(SHOW_EXPERIMENTAL_PROTOCOLS, False, type=bool)
        self.chkShowExperimentalProtocols.setChecked(show_experimental_protocols)
        self.chkShowExperimentalProtocols.stateChanged.connect(self.on_show_experimental_changed)

    def accept(self):

        if self.left_radio.isChecked():
            self.settings.setValue(DOCK_WIDGET_LOCATION, 'left')
        else:
            self.settings.setValue(DOCK_WIDGET_LOCATION, 'right')

        if self.chk_remove_layers_on_close.isChecked():
            self.settings.setValue(REMOVE_LAYERS_ON_CLOSE, True)
        else:
            self.settings.setValue(REMOVE_LAYERS_ON_CLOSE, False)

        if self.txt_path_export.text() != '':
            self.settings.setValue(DEFAULT_EXPORT_PATH, self.txt_path_export.text())
        else:
            self.settings.setValue(DEFAULT_EXPORT_PATH, '')

        if self.txt_protocol_folder.text() != '':
            self.settings.setValue(LOCAL_PROTOCOL_FOLDER, self.txt_protocol_folder.text())
        else:
            self.settings.setValue(LOCAL_PROTOCOL_FOLDER, '')

        self.settings.setValue(SHOW_EXPERIMENTAL_PROTOCOLS, self.chkShowExperimentalProtocols.isChecked())

        super().accept()

    def select_export_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select default export path")
        if path:
            self.txt_path_export.setText(path)

    def select_protocol_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select local protocol folder")
        if path:
            self.txt_protocol_folder.setText(path)

    def on_show_experimental_changed(self, state):
        if state == Qt.Checked:
            QMessageBox.warning(self, "Experimental Protocols", "Experimental protocols are protocols that are still under development and testing. They may not be fully functional and can change without notice. Please backup your project before using and proceed with caution.")

    def setup_ui(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

        self.vert = QVBoxLayout(self)
        self.setLayout(self.vert)
        self.tabs = QTabWidget()
        self.vert.addWidget(self.tabs)

        self.vertGeneral = QVBoxLayout()
        
        horiz_export_path = QHBoxLayout()
        self.vertGeneral.addLayout(horiz_export_path)

        lbl_path_export = QLabel("Default Export Path")
        horiz_export_path.addWidget(lbl_path_export)

        self.txt_path_export = QLineEdit()
        self.txt_path_export.setReadOnly(True)
        horiz_export_path.addWidget(self.txt_path_export)

        btn_path_export = QPushButton("...")
        btn_path_export.clicked.connect(self.select_export_path)
        horiz_export_path.addWidget(btn_path_export)

        btn_clear_path_export = QPushButton("Clear")
        btn_clear_path_export.clicked.connect(lambda: self.txt_path_export.setText(''))
        horiz_export_path.addWidget(btn_clear_path_export)

        self.chk_remove_layers_on_close = QCheckBox("Remove QRiS Project map layers on project close")
        self.chk_remove_layers_on_close.setToolTip("Check this box to remove all layers from the project when it is closed.")
        self.vertGeneral.addWidget(self.chk_remove_layers_on_close)
        
        self.grid = QGridLayout()

        self.label = QLabel("Default Dock widget location")
        self.grid.addWidget(self.label, 0, 0, 1, 2)

        self.left_radio = QRadioButton("Dock to left")
        self.right_radio = QRadioButton("Dock to right")
        self.grid.addWidget(self.left_radio, 1, 0)
        self.grid.addWidget(self.right_radio, 1, 1)

        self.vertGeneral.addLayout(self.grid)
        self.vertGeneral.addStretch(1)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.vert.addWidget(self.button_box)

        self.tabSettings = QWidget()
        self.tabs.addTab(self.tabSettings, "General")
        self.tabSettings.setLayout(self.vertGeneral)

        self.protocol_layout = QVBoxLayout()

        self.horiz_protocol_folder = QHBoxLayout()
        self.protocol_layout.addLayout(self.horiz_protocol_folder)

        lbl_protocol_folder = QLabel("Local Custom Protocols Folder")
        self.horiz_protocol_folder.addWidget(lbl_protocol_folder)
        self.txt_protocol_folder = QLineEdit()
        self.txt_protocol_folder.setReadOnly(True)
        self.txt_protocol_folder.setToolTip("Select an optional folder to store custom protocols.")
        self.horiz_protocol_folder.addWidget(self.txt_protocol_folder)
        btn_protocol_folder = QPushButton("...")
        btn_protocol_folder.clicked.connect(self.select_protocol_folder)
        self.horiz_protocol_folder.addWidget(btn_protocol_folder)

        self.chkShowExperimentalProtocols = QCheckBox("Show experimental protocols")
        self.chkShowExperimentalProtocols.setToolTip("Check this box to show experimental protocols in the protocol list. Experimental protocols are protocols that are still under development and testing.")
        self.protocol_layout.addWidget(self.chkShowExperimentalProtocols)

        self.protocol_layout.addStretch(1)
        self.protocol_layout.setAlignment(Qt.AlignTop)

        self.tabProtocols = QWidget()
        self.tabProtocols.setLayout(self.protocol_layout)
        self.tabs.addTab(self.tabProtocols, "Protocols")
