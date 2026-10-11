from qgis.core import QgsCoordinateTransform, QgsProject
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QApplication, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from ...lib.data_exchange import browse_data_exchange
from ...QRiS.settings import CONSTANTS, Settings
from .BaseWidget import BaseWidget
from .WizardStatus import STEP_UNKNOWN


class ContextPage(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel(
            "The NWP package should include maps that illustrate the location and context of your project. "
            "To facilitate this, you can specify a Riverscapes Context project on the Riverscapes Data Exchange. "
            "This project contains various layers that provide valuable context for your NWP submission such as watershed boundaries, stream networks, and land cover.\n\n"
            "First, use the button below to add your project extent to the map. Next, click the button open the Riverscapes Data Exchange, centred on your project area. "
            "Finally, copy the project ID for the relevant Riverscapes Context Project and paste it below.\n\n"
            "Once you have the Riverscapes Context Project ID, you can copy it, and use it in the Riverscapes Viewer 'Open Remote Project' feature to load layers into the current map."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addSpacing(20)

        # Include a button that adds the project extent layer to the current map.
        add_project_button = QPushButton("Add Project Extent Layer To Map")
        add_project_button.setToolTip("Add the project extent layer to the current map.")
        add_project_button.clicked.connect(self.add_project_extent_to_map)
        layout.addWidget(add_project_button)

        open_data_exchange_button = QPushButton("Open Riverscapes Data Exchange At Project Location")
        open_data_exchange_button.setToolTip("Open the Riverscapes Data Exchange at the project location, filtered to Riverscapes Context projects.")
        open_data_exchange_button.clicked.connect(self.open_data_exchange)
        layout.addWidget(open_data_exchange_button)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        # Include a textbox for the RSContext remote project ID
        self.project_id_textbox = QLineEdit()
        self.project_id_textbox.setPlaceholderText("Copy and paste the Riverscapes Context Project ID here")
        self.project_id_textbox.textChanged.connect(self.on_text_changed)
        hbox.addWidget(self.project_id_textbox)

        self.copy_project_id_button = QPushButton()
        self.copy_project_id_button.setToolTip("Copy the Riverscapes Context Project ID to the clipboard.")
        self.copy_project_id_button.setIcon(QIcon(":plugins/qris_toolbar/copy_content"))
        self.copy_project_id_button.setMaximumWidth(30)
        self.copy_project_id_button.setEnabled(False)
        self.copy_project_id_button.clicked.connect(lambda: QApplication.clipboard().setText(self.project_id_textbox.text()))
        hbox.addWidget(self.copy_project_id_button)

        self.open_existing_button = QPushButton()
        self.open_existing_button.setToolTip("Open an existing Riverscapes Context project using the provided project ID.")
        self.open_existing_button.clicked.connect(self.open_existing_project)
        self.open_existing_button.setIcon(QIcon(":plugins/qris_toolbar/open"))
        self.open_existing_button.setMaximumWidth(30)
        hbox.addWidget(self.open_existing_button)

        layout.addStretch()

    def get_status(self) -> int:
        return STEP_UNKNOWN

    def on_text_changed(self):
        self.contentChanged.emit()

        has_id = bool(self.project_id_textbox.text())
        self.copy_project_id_button.setEnabled(has_id)
        self.open_existing_button.setEnabled(has_id)

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        super()._save_data(
            "contextProjectId",
            {
                "projectId": self.project_id_textbox.text(),
            },
        )

    def refresh_data(self):
        """Attempt to load riverscapes context ID if it is already entered."""

        data = self.load_data("contextProjectId")
        project_id = data.get("projectId", "")
        self.project_id_textbox.setText(project_id if project_id is not None else "")

    def open_data_exchange(self) -> None:
        # Browse data exchange Riverscapes Context projects for the NWP project extent

        canvas = Settings().iface.mapCanvas()
        browse_data_exchange(canvas, project_type="rscontext")

    def open_existing_project(self) -> None:
        """Open an existing Riverscapes Context project using the provided project ID."""
        project_id = self.project_id_textbox.text()
        if not project_id:
            return

        web_viewer_url = f"{CONSTANTS['warehouseUrl']}/rv/{project_id}"
        QDesktopServices.openUrl(QUrl(web_viewer_url))

    def add_project_extent_to_map(self) -> None:
        """Add the project extent layer (selected on the Location step) to the map."""
        self.add_to_map("projectExtent")

    def zoom_to_project_extent(self) -> None:
        """Zoom the map canvas to the project extent layer, adding it to the map first if needed."""
        layer = self.add_to_map("projectExtent")
        if layer is None:
            return

        canvas = Settings().iface.mapCanvas()
        if layer.crs() != canvas.mapSettings().destinationCrs():
            transform = QgsCoordinateTransform(layer.crs(), canvas.mapSettings().destinationCrs(), QgsProject.instance())
            extent = transform.transformBoundingBox(layer.extent())
        else:
            extent = layer.extent()

        # Expand slightly to prevent a tight fit
        extent.scale(1.1)
        canvas.setExtent(extent)
        canvas.refresh()
