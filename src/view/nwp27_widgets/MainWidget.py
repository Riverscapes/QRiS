from importlib import import_module

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QComboBox, QStackedWidget, QVBoxLayout, QWidget

from .BaseWidget import BaseWidget
from .WizardStatus import STEP_COMPLETE, STEP_INCOMPLETE, STEP_UNKNOWN

STEPS = [
    {"title": "Project Title", "class": "ProjectTitlePage"},
    {"title": "Permittee", "class": "PermitteePage"},
    {"title": "Location", "class": "LocationPage"},
    {"title": "Generate Contextual Reports", "class": "ReportPage"},
    {"title": "Project Conditions", "class": "ProjectConditionsPage"},
    {
        "title": "Endangered Species Act (ESA) Relevance",
        "class": "GeneralConditionPage",
        "key": "esaRelevance",
        "description": "Ensures the activity will not jeopardize threatened or endangered species or adversely modify designated critical habitat. Compliance may require consultation with the U.S. Fish and Wildlife Service or NOAA Fisheries.",
    },
    {
        "title": "Historic Properties or Tribal Cultural Artifacts",
        "class": "GeneralConditionPage",
        "key": "historicProperties",
        "description": "Requires that activities do not affect properties listed or eligible for listing on the National Register of Historic Places. May require consultation with State Historic Preservation Officers or Tribal Historic Preservation Officers.",
    },
    {
        "title": "Water Quality Certification (WQC)",
        "class": "GeneralConditionPage",
        "key": "waterQuality",
        "description": "Under Section 401 of the Clean Water Act is required for any NWP activity that may result in a discharge from a point source into waters of the United States, unless previously granted or waived by the certifying authority. The permittee must comply with any conditions of a granted WQC.",
    },
    {
        "title": "Wild and Scenic Rivers",
        "class": "GeneralConditionPage",
        "key": "wildScenicRivers",
        "description": "No activity may occur in a designated Wild and Scenic River or study river unless the appropriate federal agency with direct management responsibility has determined in writing that the proposed activity will not adversely affect the river’s designation or study status.",
    },
    {
        "title": "Adaptive Management Plan",
        "class": "AdaptivePage",
        "key": "adaptiveManagementPlan",
        "description": "Outlines the adaptive management plan for the project, detailing how the project will be adjusted based on monitoring results and changing conditions.",
    },
    {
        "title": "Monitoring and Reporting",
        "class": "MonitoringPage",
        "key": "monitoringAndReporting",
        "description": "Details the monitoring and reporting plans for the project.",
    },
    {"title": "Reaches", "class": "ReachesPage"},
    {"title": "Map Layouts", "class": "LayoutPage"},
    {"title": "Attachments", "class": "AttachmentsPage"},
    {"title": "Export NWP27 Package", "class": "PackagePage"},
]


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())

        # Add a dropdown for the steps with icons
        self.dropdown = QComboBox()
        for step in STEPS:
            self.dropdown.addItem(step["title"])
        self.layout().addWidget(self.dropdown)

        # Stacked widget holds one page per step; only the selected one is shown
        self.stack = QStackedWidget()
        self.layout().addWidget(self.stack)

        # Map step index -> page widget so the stack and dropdown never drift
        self._pages: dict[int, QWidget] = {}

        # Push all widgets to the top, leaving extra space at the bottom
        self.layout().addStretch()

        # Eagerly create all pages so every get_status() is available at startup.
        # Data-dependent operations (refresh_data, configure pages, update icons)
        # happen in configure() once db_path and design_id are known.
        for i in range(len(STEPS)):
            self._create_page(i)

        self.dropdown.currentIndexChanged.connect(self.on_step_changed)

    def configure(self, db_path: str, design_id: int) -> None:
        self.db_path = db_path
        self.design_id = design_id

        # Now that we have real data, configure each page
        for page in self._pages.values():
            if hasattr(page, "configure"):
                page.configure(db_path, design_id)

        # Refresh data on all pages so statuses are computed from real DB state
        for page in self._pages.values():
            if hasattr(page, "refresh_data"):
                page.refresh_data()

        self.update_step_icons()
        self.on_step_changed(0)

    def _create_page(self, index: int) -> QWidget:
        """Create the page widget for the given step index, add it to the stack, and connect signals."""
        step = STEPS[index]
        class_name = step["class"]
        page_class = getattr(import_module(f"..{class_name}", __name__), class_name)
        if class_name == "GeneralConditionPage":
            page = page_class(key=step["key"], title=step["title"], description=step["description"])
        else:
            page = page_class()
        self._pages[index] = page
        self.stack.addWidget(page)
        if hasattr(page, "contentChanged"):
            page.contentChanged.connect(lambda idx=index: self.update_step_icons())
        return page

    def on_step_changed(self, index: int) -> None:
        """Show the page for the selected step, creating it on first use."""
        if index < 0 or index >= len(STEPS):
            return

        # Save the data of the page that is about to be hidden
        current: BaseWidget = self.stack.currentWidget()
        if current is not None and hasattr(current, "serialize"):
            current.serialize()

        # Create the page if it hasn't been created yet (shouldn't happen with eager init)
        page = self._pages.get(index)
        if page is None:
            page = self._create_page(index)

        # Load the data of the page that is about to be shown
        if hasattr(page, "refresh_data"):
            page.refresh_data()

        # Update the step icon immediately on load/refresh
        self.update_step_icons()

        self.stack.setCurrentWidget(page)

    def update_step_icons(self) -> None:
        """Update all dropdown menu item icons based on every step's get_status() outcome.

        Loops over all created pages so that steps whose status depends on other
        steps are always up to date regardless of which page emitted the signal.
        """
        for idx, page in self._pages.items():
            if page is not None and hasattr(page, "get_status"):
                status = page.get_status()
                if status == STEP_COMPLETE:
                    icon_path = ":/plugins/qris_toolbar/check"
                elif status == STEP_UNKNOWN:
                    icon_path = ":/plugins/qris_toolbar/none"
                elif status == STEP_INCOMPLETE:
                    icon_path = ":/plugins/qris_toolbar/cancel"

                self.dropdown.setItemIcon(idx, QIcon(icon_path))

    def change_step_status(self):
        pass
