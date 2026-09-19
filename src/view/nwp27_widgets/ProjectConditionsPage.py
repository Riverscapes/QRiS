from qgis.PyQt.QtWidgets import QFormLayout, QPlainTextEdit

from .BaseWidget import BaseWidget
from .WizardStatus import STEP_COMPLETE, STEP_INCOMPLETE


class ProjectConditionsPage(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setTitle("Project Conditions")

        layout = QFormLayout()
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.setLayout(layout)

        self.project_conditions_input = QPlainTextEdit()
        self.project_conditions_input.setTabChangesFocus(True)
        self.project_conditions_input.setPlaceholderText("What are the current conditions of the project area? What needs to be addressed?")
        self.project_conditions_input.textChanged.connect(self.on_text_changed)
        layout.addRow("Conditions", self.project_conditions_input)

        self.project_objectives_input = QPlainTextEdit()
        self.project_objectives_input.setTabChangesFocus(True)
        self.project_objectives_input.setPlaceholderText("What are you trying to achieve with this project? What are the objectives?")
        self.project_objectives_input.textChanged.connect(self.on_text_changed)
        layout.addRow("Objectives", self.project_objectives_input)

        # Register field. The '*' makes it mandatory before "Next" becomes enabled!
        # self.registerField("project_conditions", self.project_conditions_input)
        # self.registerField("project_objectives", self.project_objectives_input)

    def get_status(self) -> int:
        """Return the status of the page. This can be used to determine if the page is complete."""

        # For example, you can check if the text fields are not empty
        if self.project_conditions_input.toPlainText() and self.project_objectives_input.toPlainText():
            return STEP_COMPLETE
        else:
            return STEP_INCOMPLETE

    def on_text_changed(self):
        """Handle text changes in the input fields."""
        self.contentChanged.emit()

    def refresh_data(self):

        data = self.load_data("projectConditions")
        self.project_conditions_input.setPlainText(data.get("conditions", ""))
        self.project_objectives_input.setPlainText(data.get("objectives", ""))

    def serialize(self) -> None:
        super()._save_data("projectConditions", {"conditions": self.project_conditions_input.toPlainText().strip(), "objectives": self.project_objectives_input.toPlainText().strip()})
