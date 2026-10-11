from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from .WizardStatus import STEP_COMPLETE, STEP_INCOMPLETE


class LocationWidget(QWidget):
    # Emitted when the "Add to Map" button is clicked, carrying the ID of the
    # currently selected layer so the parent widget can add it to the map.
    addToMap = pyqtSignal(int)

    def __init__(self, include_select: bool = True, is_mandatory: bool = True, parent=None):
        super().__init__(parent)

        self.include_select = include_select
        self.is_mandatory = is_mandatory

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.cbo_layers = QComboBox()
        layout.addWidget(self.cbo_layers, 1)

        if self.include_select:
            self.cbo_layers.addItem("--- Select ---")

        self.cmd_add_layer = QPushButton()
        self.cmd_add_layer.setIcon(QIcon(":plugins/qris_toolbar/add_to_map"))
        self.cmd_add_layer.setToolTip("Add To Map")
        self.cmd_add_layer.clicked.connect(self.on_add_layer_clicked)
        layout.addWidget(self.cmd_add_layer)

        self.cmd_layer_info = QPushButton()
        self.cmd_layer_info.setIcon(QIcon(":plugins/qris_toolbar/help"))
        self.cmd_layer_info.setToolTip("Info")
        self.cmd_layer_info.clicked.connect(self.on_layer_info_clicked)
        layout.addWidget(self.cmd_layer_info)

    def get_status(self) -> int:
        if self.is_mandatory is False:
            return STEP_COMPLETE

        if self.include_select is True:
            # Index > 0 means a real layer (not the "--- Select ---" placeholder)
            if self.cbo_layers.currentIndex() > 0:
                return STEP_COMPLETE
        else:
            if self.cbo_layers.currentIndex() >= 0:
                return STEP_COMPLETE

        return STEP_INCOMPLETE

    def on_add_layer_clicked(self):
        self.addToMap.emit(self.cbo_layers.currentData())

    def on_layer_info_clicked(self):
        pass
