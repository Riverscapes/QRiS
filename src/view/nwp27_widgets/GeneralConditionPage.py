from qgis.PyQt.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QRadioButton,
    QVBoxLayout,
)

from .BaseWidget import BaseWidget
from .WizardStatus import STEP_COMPLETE, STEP_INCOMPLETE


class GeneralConditionPage(BaseWidget):
    def __init__(self, db_path: str, design_id: str, key: str, title: str, description: str, parent=None):
        super().__init__(db_path, design_id, parent)
        self.key = key
        self.title = title
        self.description = description

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.intro_label = QLabel(self.description)
        self.intro_label.setWordWrap(True)
        layout.addWidget(self.intro_label)

        radio_layout = QHBoxLayout()

        self.relevant_radio = QRadioButton("Relevant")
        self.relevant_radio.setChecked(True)
        self.relevant_radio.toggled.connect(self.on_text_changed)
        self.not_relevant_radio = QRadioButton("Not Relevant")
        self.not_relevant_radio.toggled.connect(self.on_text_changed)
        radio_layout.addWidget(self.relevant_radio)
        radio_layout.addWidget(self.not_relevant_radio)

        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        layout.addLayout(form_layout)

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.relevant_radio)
        self.button_group.addButton(self.not_relevant_radio)
        form_layout.addRow("", radio_layout)

        self.status_input = QPlainTextEdit()
        self.status_input.setTabChangesFocus(True)
        self._constrain_text_edit(self.status_input)
        self.status_input.textChanged.connect(self.on_text_changed)
        form_layout.addRow("Status", self.status_input)

        self.notes_inputs = QPlainTextEdit()
        self.notes_inputs.setTabChangesFocus(True)
        self._constrain_text_edit(self.notes_inputs)
        self.notes_inputs.textChanged.connect(self.on_text_changed)
        form_layout.addRow("Notes", self.notes_inputs)

    def get_status(self) -> int:

        if self.not_relevant_radio.isChecked():
            return STEP_COMPLETE

        if self.status_input.toPlainText() and self.notes_inputs.toPlainText():
            return STEP_COMPLETE
        elif self.status_input.toPlainText() or self.notes_inputs.toPlainText():
            return STEP_INCOMPLETE
        return STEP_INCOMPLETE

    def on_text_changed(self):
        self.status_input.setEnabled(self.relevant_radio.isChecked())
        self.notes_inputs.setEnabled(self.relevant_radio.isChecked())
        self.contentChanged.emit()

    def refresh_data(self):

        data = self.load_data(self.key)

        relevant = data.get("relevant", True)
        if relevant:
            self.relevant_radio.setChecked(True)
        else:
            self.not_relevant_radio.setChecked(True)

        self.status_input.setPlainText(data.get("status", ""))
        self.notes_inputs.setPlainText(data.get("notes", ""))

    def serialize(self) -> None:
        super()._save_data(self.key, {"relevant": self.relevant_radio.isChecked(), "status": self.status_input.toPlainText().strip(), "notes": self.notes_inputs.toPlainText().strip()})
