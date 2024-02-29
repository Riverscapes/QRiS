

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QDialog, QRadioButton, QVBoxLayout, QDialogButtonBox, QLabel


class FrmSettings(QDialog):
    def __init__(self, settings: QSettings, dock_widget_location: str, default_dock_widget_location:str):
        super().__init__()

        self.settings = settings
        self.dock_widget_location = dock_widget_location
        self.default_dock_widget_location = default_dock_widget_location

        self.setWindowTitle("QRiS Settings")
        self.setup_ui()

        # Get the dockwidget location from the settings
        dock_location = settings.value(self.dock_widget_location, self.default_dock_widget_location)

        if dock_location == 'left':
            self.left_radio.setChecked(True)
        else:
            self.right_radio.setChecked(True)

    def accept(self):


        if self.left_radio.isChecked():
            self.settings.setValue(self.dock_widget_location, 'left')
        else:
            self.settings.setValue(self.dock_widget_location, 'right')

        super().accept()


    def setup_ui(self):

        self.layout = QVBoxLayout()

        self.label = QLabel("Default Dock widget location")
        self.layout.addWidget(self.label)

        self.left_radio = QRadioButton("Dock to left")
        self.right_radio = QRadioButton("Dock to right")

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.left_radio)
        self.layout.addWidget(self.right_radio)

        # add a label to the layout to explain settings will take effect after restarting qgis
        self.layout.addWidget(QLabel("Settings will take effect after restarting QGIS"))

        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)
