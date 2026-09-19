from qgis.PyQt.QtWidgets import QComboBox, QFormLayout, QLabel, QVBoxLayout

from .BaseWidget import BaseWidget
from .DBCon import DBCon
from .LocationWidget import LocationWidget
from .WizardStatus import STEP_COMPLETE, STEP_INCOMPLETE


class LocationPage(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setTitle("Project Location")

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel(
            "The NWP27 report requires the following spatial layers. Select the appropriate layer from your QRiS project or click the 'Add New' buttons to add a new instance of the QRiS layer. You can close this wizard and return to QGiS to digitize features in each of the layer. Click the info button learn about how each of the layers is used in the NWP27 report."
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        layout.addLayout(form_layout)

        self.project_extent = LocationWidget()
        self.project_extent.cbo_layers.currentIndexChanged.connect(self.on_text_changed)
        form_layout.addRow("Project extent", self.project_extent)
        # self.load_sample_frame_layers(self.project_extent.cbo_layers, [3])

        self.reaches_input = LocationWidget()
        self.reaches_input.cbo_layers.currentIndexChanged.connect(self.on_text_changed)
        form_layout.addRow("Reaches", self.reaches_input)
        # self.load_sample_frame_layers(self.reaches_input.cbo_layers, [1])

        self.disturbance_input = LocationWidget(is_mandatory=False)
        self.disturbance_input.cbo_layers.currentIndexChanged.connect(self.on_text_changed)
        form_layout.addRow("Disturbance limits", self.disturbance_input)

        self.structures_input = LocationWidget()
        self.structures_input.cbo_layers.currentIndexChanged.connect(self.on_text_changed)
        form_layout.addRow("Structures", self.structures_input)

        self.imagery = LocationWidget(is_mandatory=False)
        self.imagery.cbo_layers.currentIndexChanged.connect(self.on_text_changed)
        form_layout.addRow("Imagery", self.imagery)
        # self.load_rasters(self.imagery.cbo_layers)

        self.catchment = LocationWidget()
        self.catchment.cbo_layers.currentIndexChanged.connect(self.on_text_changed)
        form_layout.addRow("Catchment Area", self.catchment)

        # Push all content to the top, leaving extra space at the bottom
        layout.addStretch()

    def configure(self, db_path: str, design_id: int) -> None:
        super().configure(db_path, design_id)
        self.load_sample_frame_layers(self.project_extent.cbo_layers, [3])
        self.load_sample_frame_layers(self.reaches_input.cbo_layers, [1])
        self.load_rasters(self.imagery.cbo_layers)
        self.load_catchments(self.catchment.cbo_layers)

    def get_status(self) -> int:

        widgets = [
            self.project_extent,
            self.reaches_input,
            self.disturbance_input,
            self.structures_input,
            self.imagery,
            self.catchment,
        ]

        for widget in widgets:
            if widget.get_status() != STEP_COMPLETE:
                return STEP_INCOMPLETE
        return STEP_COMPLETE

    def on_text_changed(self):
        self.contentChanged.emit()

    def load_sample_frame_layers(self, cbo: QComboBox, sample_frame_type_ids: list):
        with DBCon.connect(self.db_path) as conn:
            cursor = conn.cursor()
            placeholders = ", ".join("?" for _ in sample_frame_type_ids)
            cursor.execute(f"SELECT name, id FROM sample_frames WHERE sample_frame_type_id IN ({placeholders})", sample_frame_type_ids)

            for extent in cursor.fetchall():
                cbo.addItem(extent["name"], extent["id"])

    def load_catchments(self, cbo: QComboBox):
        with DBCon.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Note how the catchment ID is used, but the pour point name
            cursor.execute("""SELECT c.fid, pp.name
                FROM pour_points pp
                INNER JOIN catchments c on pp.fid = c.pour_point_id""")
            for catchment in cursor.fetchall():
                cbo.addItem(catchment["name"], catchment["fid"])

    def load_rasters(self, cbo: QComboBox):

        with DBCon.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, id FROM rasters")
            for raster in cursor.fetchall():
                cbo.addItem(raster["name"], raster["id"])

    def refresh_data(self):
        data = self.load_data("locations")

        self.project_extent.cbo_layers.setCurrentIndex(self.project_extent.cbo_layers.findData(data.get("projectExtent")))
        self.reaches_input.cbo_layers.setCurrentIndex(self.reaches_input.cbo_layers.findData(data.get("reaches")))
        self.disturbance_input.cbo_layers.setCurrentIndex(self.disturbance_input.cbo_layers.findData(data.get("disturbance")))
        self.structures_input.cbo_layers.setCurrentIndex(self.structures_input.cbo_layers.findData(data.get("structures")))
        self.imagery.cbo_layers.setCurrentIndex(self.imagery.cbo_layers.findData(data.get("imagery")))
        self.catchment.cbo_layers.setCurrentIndex(self.catchment.cbo_layers.findData(data.get("catchment")))

    def serialize(self) -> None:
        super()._save_data(
            "locations",
            {
                "projectExtent": self.project_extent.cbo_layers.currentData(),
                "reaches": self.reaches_input.cbo_layers.currentData(),
                "disturbance": self.disturbance_input.cbo_layers.currentData(),
                "structures": self.structures_input.cbo_layers.currentData(),
                "imagery": self.imagery.cbo_layers.currentData(),
                "catchment": self.catchment.cbo_layers.currentData(),
            },
        )
