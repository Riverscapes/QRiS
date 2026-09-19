from qgis.PyQt.QtWidgets import QFormLayout, QLineEdit

from .BaseWidget import BaseWidget
from .WizardStatus import STEP_COMPLETE, STEP_INCOMPLETE


class PermitteePage(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setTitle("Permittee Information")
        # self.setSubTitle("Please provide permittee information.")

        layout = QFormLayout()
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.setLayout(layout)

        self.permittee_name_input = QLineEdit()
        self.permittee_name_input.textChanged.connect(self.on_text_changed)
        layout.addRow("Name", self.permittee_name_input)

        self.organization_input = QLineEdit()
        self.organization_input.textChanged.connect(self.on_text_changed)
        layout.addRow("Organization", self.organization_input)

        self.address_input = QLineEdit()
        self.address_input.textChanged.connect(self.on_text_changed)
        layout.addRow("Address", self.address_input)

        self.telephone_input = QLineEdit()
        self.telephone_input.textChanged.connect(self.on_text_changed)
        layout.addRow("Telephone", self.telephone_input)

        self.permittee_email_input = QLineEdit()
        self.permittee_email_input.textChanged.connect(self.on_text_changed)
        layout.addRow("Email", self.permittee_email_input)

        # self.registerField("permittee_name", self.permittee_name_input)
        # self.registerField("organization", self.organization_input)
        # self.registerField("address", self.address_input)
        # self.registerField("telephone", self.telephone_input)
        # self.registerField("permittee_email", self.permittee_email_input)

    def get_status(self) -> int:
        if self.permittee_name_input.text() and self.organization_input.text():
            return STEP_COMPLETE
        elif self.permittee_name_input.text() or self.organization_input.text():
            return STEP_INCOMPLETE
        return STEP_INCOMPLETE

    def on_text_changed(self):
        self.contentChanged.emit()

    def refresh_data(self):

        data = self.load_data("permittee")
        self.permittee_name_input.setText(data.get("permitteeName", ""))
        self.organization_input.setText(data.get("organization", ""))
        self.address_input.setText(data.get("address", ""))
        self.telephone_input.setText(data.get("telephone", ""))
        self.permittee_email_input.setText(data.get("email", ""))

    def serialize(self) -> None:

        super()._save_data(
            "permittee",
            {"permitteeName": self.permittee_name_input.text(), "organization": self.organization_input.text(), "address": self.address_input.text(), "telephone": self.telephone_input.text(), "email": self.permittee_email_input.text()},
        )
