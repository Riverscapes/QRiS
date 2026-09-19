from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QFormLayout, QPlainTextEdit

from .BaseWidget import BaseWidget


class MonitoringPage(BaseWidget):
    contentChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setTitle("Monitoring")
        # self.setSubTitle("Please provide information about your monitoring and reporting plans.")

        layout = QFormLayout()
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.setLayout(layout)

        self.monitoring_plan_input = QPlainTextEdit()
        self.monitoring_plan_input.setTabChangesFocus(True)
        self.monitoring_plan_input.setPlaceholderText("What monitoring actions will you take to ensure the project is successful? How will you report on the project outcomes?")
        self.monitoring_plan_input.textChanged.connect(self.on_text_changed)
        layout.addRow("", self.monitoring_plan_input)

        # self.registerField("monitoring_plan", self.monitoring_plan_input)

    def get_status(self) -> int:
        if self.monitoring_plan_input.toPlainText():
            return 2
        return 0

    def on_text_changed(self):
        self.contentChanged.emit()
