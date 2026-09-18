from qgis.PyQt.QtWidgets import QFormLayout, QPlainTextEdit

from .BaseWidget import BaseWidget
from .WizardStatus import STEP_COMPLETE, STEP_INCOMPLETE


class AdaptivePage(BaseWidget):
    def __init__(self, db_path: str, design_id: str, parent=None):
        super().__init__(db_path, design_id, parent)
        # self.setTitle("Project Conditions")

        # self.setTitle("Adaptive Management Plan")
        # self.setSubTitle("This is an adaptive page that can change its content based on user input.")

        layout = QFormLayout()
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.setLayout(layout)

        self.adaptive_input = QPlainTextEdit()
        self.adaptive_input.setTabChangesFocus(True)
        self.adaptive_input.setPlaceholderText("What is your adaptive management plan? How will you adapt your project based on monitoring results?")
        self.adaptive_input.textChanged.connect(self.on_text_changed)
        layout.addRow("", self.adaptive_input)

        # self.registerField("adaptive_input", self.adaptive_input)

    def get_status(self) -> int:
        if len(self.adaptive_input.toPlainText().strip()) > 0:
            return STEP_COMPLETE
        return STEP_INCOMPLETE

    def on_text_changed(self):
        self.contentChanged.emit()

    def refresh_data(self):

        data = self.load_data("adaptiveManagementPlan")
        self.adaptive_input.setPlainText(data.get("adaptiveInput", ""))

    def serialize(self) -> None:
        super()._save_data("adaptiveManagementPlan", {"adaptiveInput": self.adaptive_input.toPlainText().strip()})
