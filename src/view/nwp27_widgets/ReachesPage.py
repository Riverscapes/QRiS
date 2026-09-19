from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .BaseWidget import BaseWidget
from .DBCon import DBCon
from .WizardStatus import STEP_COMPLETE, STEP_INCOMPLETE


class ReachesPage(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Keep track of the inputs for each reach. The keys are FID from sample_frame_features feature class.
        # The values are dictionaries containing the treatments, conditions, and objectives for each reach.
        self.reach_data = {}

        # Use a QStackedWidget to switch between the no-layer message (index 0)
        # and the actual form (index 1) on the fly, so the UI adapts when
        # the user adds or removes a reaches layer on the Location step.
        self.setLayout(QVBoxLayout())
        self.stack = QStackedWidget()
        self.layout().addWidget(self.stack)

        # --- Page 0: No layer found message ---
        no_layer_page = QWidget()
        no_layer_layout = QVBoxLayout()
        no_layer_page.setLayout(no_layer_layout)
        no_layer_label = QLabel("No reaches layer found. This step cannot be completed until you have selected a reaches layer on the 'Location' step.")
        no_layer_layout.addWidget(no_layer_label)
        no_layer_layout.addStretch()
        self.stack.addWidget(no_layer_page)  # index 0

        # --- Page 1: The actual form ---
        form_page = QWidget()
        form_layout = QFormLayout(form_page)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        h_layout = QHBoxLayout()
        previous_button = QPushButton()
        previous_button.setFixedWidth(self.BUTTON_WIDTH)
        previous_button.setIcon(QIcon("/Users/philipbailey/code/riverscapes/nwp27-wizard/assets/arrow-back.svg"))

        previous_button.clicked.connect(self.on_previous_clicked)
        h_layout.addWidget(previous_button)

        self.cbo_reaches = QComboBox()
        self.cbo_reaches.currentIndexChanged.connect(self.on_reach_changed)
        h_layout.addWidget(self.cbo_reaches, 1)

        zoom_button = QPushButton()
        zoom_button.setFixedWidth(self.BUTTON_WIDTH)
        zoom_button.setIcon(QIcon("/Users/philipbailey/code/riverscapes/nwp27-wizard/assets/zoom-in.svg"))
        zoom_button.clicked.connect(self.on_zoom_clicked)
        h_layout.addWidget(zoom_button)

        next_button = QPushButton()
        next_button.setFixedWidth(self.BUTTON_WIDTH)
        next_button.setIcon(QIcon("/Users/philipbailey/code/riverscapes/nwp27-wizard/assets/arrow-forward.svg"))

        next_button.clicked.connect(self.on_next_clicked)
        h_layout.addWidget(next_button)

        form_layout.addRow("Reach", h_layout)
        self.treatment_temp = QPlainTextEdit()
        self.treatment_temp.setTabChangesFocus(True)
        self._constrain_text_edit(self.treatment_temp)
        self.treatment_temp.textChanged.connect(self.on_text_changed)
        form_layout.addRow("Treatments", self.treatment_temp)

        self.reach_conditions_input = QPlainTextEdit()
        self.reach_conditions_input.setTabChangesFocus(True)
        self._constrain_text_edit(self.reach_conditions_input)
        self.reach_conditions_input.textChanged.connect(self.on_text_changed)
        form_layout.addRow("Conditions", self.reach_conditions_input)

        self.reach_objectives_input = QPlainTextEdit()
        self.reach_objectives_input.setTabChangesFocus(True)
        self._constrain_text_edit(self.reach_objectives_input)
        self.reach_objectives_input.textChanged.connect(self.on_text_changed)
        form_layout.addRow("Objectives", self.reach_objectives_input)

        self.stack.addWidget(form_page)  # index 1

        self.cbo_reaches.setFocus()

    def on_previous_clicked(self):
        """Navigate to the previous reach in the dropdown."""
        current = self.cbo_reaches.currentIndex()
        if current > 0:
            self.cbo_reaches.setCurrentIndex(current - 1)

    def on_next_clicked(self):
        """Navigate to the next reach in the dropdown."""
        current = self.cbo_reaches.currentIndex()
        if current < self.cbo_reaches.count() - 1:
            self.cbo_reaches.setCurrentIndex(current + 1)

    def get_status(self) -> int:

        reach_layer_id = self.get_reaches_layer()
        if reach_layer_id < 1:
            return STEP_INCOMPLETE

        # Loop over all the reaches and check if all have treatments, conditions, and objectives filled in.
        for reach_info in self.reach_data.values():
            if not isinstance(reach_info, dict):
                return STEP_INCOMPLETE
            if not (reach_info.get("treatments") and reach_info.get("conditions") and reach_info.get("objectives")):
                return STEP_INCOMPLETE

        return STEP_COMPLETE

    def on_text_changed(self):
        """Save the current text fields to the in-memory reach data and emit contentChanged.

        Use string keys so they survive JSON round-tripping through the database.
        """
        fid = self.cbo_reaches.currentData()
        if fid is not None:
            self.reach_data[str(fid)] = {
                "treatments": self.treatment_temp.toPlainText(),
                "conditions": self.reach_conditions_input.toPlainText(),
                "objectives": self.reach_objectives_input.toPlainText(),
            }
        self.contentChanged.emit()

    def on_reach_changed(self):
        """Load the newly selected reach's data into the text fields.

        Note: the previously visible reach's text was already saved to
        ``self.reach_data`` by ``on_text_changed`` on every keystroke.
        """
        fid = self.cbo_reaches.currentData()
        reach_info = self.reach_data.get(str(fid)) if fid is not None else None
        if isinstance(reach_info, dict):
            self.treatment_temp.setPlainText(reach_info.get("treatments", ""))
            self.reach_conditions_input.setPlainText(reach_info.get("conditions", ""))
            self.reach_objectives_input.setPlainText(reach_info.get("objectives", ""))
        else:
            self.treatment_temp.clear()
            self.reach_conditions_input.clear()
            self.reach_objectives_input.clear()

    def get_reaches_layer(self) -> int:
        layer_data = self.load_data("locations")
        if layer_data:
            reaches_data = layer_data.get("reaches")
            if reaches_data:
                # Return the first reach as a placeholder
                return reaches_data
        return 0

    def load_reach_polygons(self):

        reaches_id = self.get_reaches_layer()
        if reaches_id < 1:
            return

        with DBCon(self.db_path) as con:
            curs = con.cursor()
            curs.execute("SELECT fid, coalesce(display_label, fid) as label FROM sample_frame_features WHERE sample_frame_id = ?", (reaches_id,))
            self.cbo_reaches.clear()
            for row in curs.fetchall():
                self.cbo_reaches.addItem(row["label"], row["fid"])

    def refresh_data(self):
        """Switch between the no-layer message and the form, then load data if available."""
        has_layer = self.get_reaches_layer() >= 1
        self.stack.setCurrentIndex(1 if has_layer else 0)
        if has_layer:
            self.reach_data = self.load_data("reaches")
            self.load_reach_polygons()

    def serialize(self) -> None:
        """Persist the current widget values to the database."""
        if self.stack.currentIndex() == 0:
            return
        super()._save_data("reaches", self.reach_data)

    def on_zoom_clicked(self):
        """Handle the zoom button click event."""
        reaches_id = self.get_reaches_layer()
        if reaches_id < 1:
            return

        # Implement the zoom logic here, e.g., interacting with a GIS viewer
        print(f"Zooming to reach layer with ID: {reaches_id}")
