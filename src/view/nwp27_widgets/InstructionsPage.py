from qgis.PyQt.QtWidgets import (
    QLabel,
    QVBoxLayout,
)

from .BaseWidget import BaseWidget
from .WizardStatus import STEP_UNKNOWN


class InstructionsPage(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel(
            "This wizard helps you gather the information required to apply for a US Army Corps of Engineers "
            "Nationwide Permit 27 (NWP). It combines the spatial data in your QRiS project with the supporting "
            "text you enter here, to produce a package of material that can serve as a starting point for your NWP submission.\n\n"
            "Use the dropdown above to switch between steps. Some steps contain required fields and must be "
            "completed before you can proceed (indicated by a red check mark). Click the help button at the top right for more information.\n\n"
            "The final Packaging step exports everything to your computer in open, reusable HTML, image, and "
            "PDF formats for your NWP submission."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addSpacing(20)

        self.add_link("NWP Conditions, Further Information & Defintions", "https://usace.contentdm.oclc.org/utils/getfile/collection/p16021coll9/id/3209")
        self.add_link("USACE Reissuance and Modifications of NWP", "https://www.federalregister.gov/documents/2026/01/08/2026-00121/reissuance-and-modification-of-nationwide-permits")

        layout.addStretch()

    def get_status(self) -> int:
        return STEP_UNKNOWN

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def add_link(self, display_text: str, url: str) -> None:
        """Add a clickable hyperlink label that opens the URL in the system browser."""
        link = QLabel(f'<a href="{url}">{display_text}</a>')
        link.setOpenExternalLinks(True)
        link.setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(link)
