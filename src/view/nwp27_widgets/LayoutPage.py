from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .BaseWidget import BaseWidget
from .WizardStatus import STEP_UNKNOWN

LAYOUTS = [
    ("Project Elements Layout", "Description for Layout 1", "machine1"),
    ("Habitat Zones & Conditions", "Description for Layout 2", "machine2"),
    ("Project Summary", "Description for Layout 3", "machine3"),
    ("Reach Elements & Expected Outcomes", "Description for Layout 3", "machine4"),
]


class LayoutPage(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setTitle("Project Location")

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel("layout explanation")
        label.setWordWrap(True)
        layout.addWidget(label)

        for layout_name, description, machine_code in LAYOUTS:
            h_layout = QHBoxLayout()
            layout.addLayout(h_layout)

            name_label = QLabel(layout_name)
            h_layout.addWidget(name_label)

            description_label = QLabel(description)
            description_label.setWordWrap(True)
            h_layout.addWidget(description_label)

            # add three buttons for opening, saving and printing each layout
            open_button = QPushButton()
            open_button.setToolTip("Open")
            open_button.setFixedWidth(self.BUTTON_WIDTH)
            open_button.setIcon(QIcon("/Users/philipbailey/code/riverscapes/nwp27-wizard/assets/open.svg"))
            open_button.clicked.connect(lambda _, name=layout_name, code=machine_code: self.open_layout(name, code))
            h_layout.addWidget(open_button)

            save_button = QPushButton()
            save_button.setToolTip("Save")
            save_button.setFixedWidth(self.BUTTON_WIDTH)
            save_button.setIcon(QIcon("/Users/philipbailey/code/riverscapes/nwp27-wizard/assets/save.svg"))
            save_button.clicked.connect(lambda _, name=layout_name, code=machine_code: self.save_layout(name, code))
            h_layout.addWidget(save_button)

            print_button = QPushButton()
            print_button.setToolTip("Print")
            print_button.setFixedWidth(self.BUTTON_WIDTH)
            print_button.setIcon(QIcon("/Users/philipbailey/code/riverscapes/nwp27-wizard/assets/print.svg"))
            print_button.clicked.connect(lambda _, name=layout_name, code=machine_code: self.print_layout(name, code))
            h_layout.addWidget(print_button)

        # stretch
        layout.addStretch()

    def get_status(self) -> int:
        return STEP_UNKNOWN

    def on_text_changed(self):
        self.contentChanged.emit()

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def open_layout(self, name: str, machine_code: str) -> None:
        pass

    def save_layout(self, name: str, machine_code: str) -> None:
        pass

    def print_layout(self, name: str, machine_code: str) -> None:
        pass
