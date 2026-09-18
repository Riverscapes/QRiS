from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from .WizardStatus import STEP_COMPLETE, STEP_INCOMPLETE


class LocationWidget(QWidget):
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
        self.cmd_add_layer.setIcon(QIcon("/Users/philipbailey/code/riverscapes/nwp27-wizard/assets/add.svg"))
        self.cmd_add_layer.setToolTip("Add New")
        self.cmd_add_layer.clicked.connect(self.on_add_layer_clicked)
        layout.addWidget(self.cmd_add_layer)

        self.cmd_layer_info = QPushButton()
        self.cmd_layer_info.setIcon(QIcon("/Users/philipbailey/code/riverscapes/nwp27-wizard/assets/about.svg"))
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
        pass

    def on_layer_info_clicked(self):
        pass
