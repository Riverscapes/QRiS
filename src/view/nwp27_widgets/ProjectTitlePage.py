import datetime

from qgis.PyQt.QtWidgets import QDateEdit, QFormLayout, QLineEdit

from .BaseWidget import BaseWidget
from .WizardStatus import STEP_COMPLETE, STEP_INCOMPLETE

_TODAY = datetime.datetime.now(datetime.timezone.utc).date()

MINIMUM_DATE = datetime.date(2000, 1, 1)
MAXIMUM_DATE = datetime.date(_TODAY.year + 30, 12, 31)


class ProjectTitlePage(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setWindowTitle("Project Title")
        # self.setSubTitle("Please provide the project title and relevant dates.")

        layout = QFormLayout()
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.setLayout(layout)

        self.title_input = QLineEdit()
        self.title_input.textChanged.connect(self.on_text_changed)
        self.title_input.setMaxLength(self.LINE_EDIT_MAX_LENGTH)
        self.application_date = QDateEdit()
        self.application_date.setCalendarPopup(True)
        self.application_date.setMinimumDate(MINIMUM_DATE)
        self.application_date.setMaximumDate(MAXIMUM_DATE)
        self.application_date.setDate(_TODAY)
        self.implementation_start = QDateEdit()
        self.implementation_start.setCalendarPopup(True)
        self.implementation_start.setMinimumDate(MINIMUM_DATE)
        self.implementation_start.setMaximumDate(MAXIMUM_DATE)
        self.implementation_end = QDateEdit()
        self.implementation_end.setCalendarPopup(True)
        self.implementation_end.setMinimumDate(MINIMUM_DATE)
        self.implementation_end.setMaximumDate(MAXIMUM_DATE)

        layout.addRow("Project title", self.title_input)
        layout.addRow("Application date", self.application_date)
        layout.addRow("Implementation start", self.implementation_start)
        layout.addRow("Implementation end", self.implementation_end)
        self.setLayout(layout)

    def get_status(self) -> int:
        """Return the status of the page. This can be used to determine if the page is complete."""

        # For example, you can check if the title field is not empty
        if self.title_input.text():
            return STEP_COMPLETE
        else:
            return STEP_INCOMPLETE

    def on_text_changed(self):
        """Handle text changes in the input fields."""
        self.contentChanged.emit()

    def refresh_data(self):

        data = self.load_data("projectTitle")
        self.title_input.setText(data.get("title", ""))
        self.application_date.setDate(self._parse_date(data.get("applicationDate")))
        self.implementation_start.setDate(self._parse_date(data.get("implementationStart")))
        self.implementation_end.setDate(self._parse_date(data.get("implementationEnd")))

    @staticmethod
    def _parse_date(value) -> datetime.date:
        """Parse a yyyy-mm-dd string (or date) back into a date, defaulting to today."""
        if isinstance(value, str):
            try:
                return datetime.date.fromisoformat(value)
            except ValueError:
                pass
        elif isinstance(value, datetime.date):
            return value
        return _TODAY

    def serialize(self) -> None:
        super()._save_data(
            "projectTitle",
            {
                "title": self.title_input.text(),
                "applicationDate": self.application_date.date().toPyDate().isoformat(),
                "implementationStart": self.implementation_start.date().toPyDate().isoformat(),
                "implementationEnd": self.implementation_end.date().toPyDate().isoformat(),
            },
        )
