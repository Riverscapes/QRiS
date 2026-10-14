from abc import abstractmethod
import json
import os

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QMessageBox, QPlainTextEdit, QWidget

from ...model.sample_frame import SampleFrame
from ...QRiS.settings import Settings
from .DBCon import DBCon


class BaseWidget(QWidget):
    contentChanged = pyqtSignal()

    LINE_EDIT_MAX_LENGTH = 255
    TEXT_EDIT_MAX_LENGTH = 1024

    BUTTON_WIDTH = 32

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_path = None
        self.design_id = None
        self._project = None

        # Give QLineEdit a visible border (QTextEdit has one by default)
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                padding: 2px 4px;
            }
        """)

    def configure(self, db_path: str, design_id: int) -> None:
        """
        Store the QRiS GeoPackage path and the design ID.
        Note that this can't happen as part of the constructor because
        dockable windows get constructed at different time to the widgets.
        """
        self.db_path = db_path
        self.design_id = design_id

    def set_project(self, project) -> None:
        """Set the shared Project instance so layers can be added to the map."""
        self._project = project

    def add_to_map(self, key: str):
        """Add the layer selected for the given location key to the map, if not already there.

        The layer id is read from the saved "locations" data (see LocationPage.serialize),
        so the caller only needs to pass the key. The behaviour depends on the key:
        - projectExtent / reaches / disturbance: sample frame layers
        - structures: the event's structure points layer
        - imagery: a raster layer
        - catchment: the catchment (and pour point) layers

        Returns the map layer that was added (or the existing one), or None if it
        could not be added.
        """
        if self._project is None:
            QMessageBox.warning(self, "QRiS", "The QRiS project is not loaded, so the layer cannot be added to the map.")
            return None

        layer_id = self.load_data("locations").get(key)
        if not layer_id:
            QMessageBox.warning(self, "QRiS", "Please select a layer first.")
            return None

        map_manager = self._get_map_manager()
        if map_manager is None:
            QMessageBox.warning(self, "QRiS", "The QRiS project is not loaded, so the layer cannot be added to the map.")
            return None

        try:
            if key in ("projectExtent", "reaches", "disturbance"):
                return self._add_sample_frame_layer(map_manager, layer_id)
            elif key == "structures":
                return self._add_structures_layer(map_manager, layer_id)
            elif key == "imagery":
                return map_manager.build_raster_layer(self._project.rasters[layer_id])
            elif key == "catchment":
                return self._add_catchment_layer(map_manager, layer_id)
            else:
                raise KeyError(key)
        except KeyError:
            QMessageBox.warning(self, "QRiS", "Please select a layer first.")
            return None

    def _get_map_manager(self):
        """Find the map manager on the main window, or None if the project is not loaded."""
        main_window = Settings().iface.mainWindow()
        for widget in main_window.findChildren(QWidget):
            if hasattr(widget, "map_manager") and widget.map_manager is not None:
                return widget.map_manager
        return None

    def _add_sample_frame_layer(self, map_manager, layer_id: int):
        """Build (or reuse) the sample frame layer and add it to the map."""
        frame = self._project.sample_frames.get(layer_id) or self._project.aois.get(layer_id) or self._project.valley_bottoms.get(layer_id)
        if frame is None:
            raise KeyError(layer_id)

        if frame.sample_frame_type == SampleFrame.AOI_SAMPLE_FRAME_TYPE:
            return map_manager.build_aoi_layer(frame)
        elif frame.sample_frame_type == SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE:
            return map_manager.build_valley_bottom_layer(frame)
        else:
            return map_manager.build_sample_frame_layer(frame)

    def _add_structures_layer(self, map_manager, layer_id: int):
        """Build (or reuse) the structure points layer for this design event and add it to the map."""
        event = self._project.events.get(self.design_id)
        if event is None:
            raise KeyError(layer_id)

        event_layer = next((el for el in event.event_layers if el.id == layer_id), None)
        if event_layer is None:
            raise KeyError(layer_id)

        return map_manager.build_event_single_layer(event, event_layer)

    def _add_catchment_layer(self, map_manager, layer_id: int):
        """Build (or reuse) the catchment and pour point layers and add them to the map.

        The combo stores the pour point id (see LocationPage.load_catchments).
        """
        pour_point = self._project.pour_points.get(layer_id)
        if pour_point is None:
            raise KeyError(layer_id)

        return map_manager.build_pour_point_map_layer(pour_point)

    def load_data(self, key: str) -> dict:

        with DBCon(self.db_path) as con:
            curs = con.cursor()
            curs.execute("SELECT metadata as info FROM events WHERE id = ?", (self.design_id,))
            row = curs.fetchone()
            if not row:
                return {}

            metadata = row.get("info")
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

                nwp27 = metadata.get("nwp27") if isinstance(metadata, dict) else {}
                if isinstance(nwp27, dict):
                    return nwp27.get(key, {})

            return {}

    @abstractmethod
    def deserialize(self, data: dict) -> None:
        """Parse the given data and populate the widget controls."""
        raise NotImplementedError

    @abstractmethod
    def serialize(self) -> None:
        """Gather the data from the widgets and return it as a dictionary ready to be saved to the database"""
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> int:
        """Return the status of the widget as an integer.
        See WizardStatus.py constants for possible values
        """
        raise NotImplementedError

    def _constrain_text_edit(self, text_edit: QPlainTextEdit, max_length: int = TEXT_EDIT_MAX_LENGTH) -> None:
        """Constrain a QPlainTextEdit to the given max length by truncating on text changes.

        QPlainTextEdit does not have a built-in setMaxLength(), so this method
        connects to textChanged and truncates the content if it exceeds the limit.
        """
        max_length = max_length or self.TEXT_EDIT_MAX_LENGTH

        def on_text_changed():
            if len(text_edit.toPlainText()) > max_length:
                cursor = text_edit.textCursor()
                pos = cursor.position()
                text_edit.blockSignals(True)
                text_edit.setPlainText(text_edit.toPlainText()[:max_length])
                cursor = text_edit.textCursor()
                cursor.setPosition(min(pos, max_length))
                text_edit.setTextCursor(cursor)
                text_edit.blockSignals(False)

        text_edit.textChanged.connect(on_text_changed)

    def _save_data(self, key: str, nwp_data: dict) -> None:

        with DBCon(self.db_path) as con:
            curs = con.cursor()

            try:
                curs.execute("SELECT metadata FROM events WHERE id = ?", (self.design_id,))
                row = curs.fetchone()
                if not row:
                    raise ValueError(f"No event found with id {self.design_id}")

                metadata = row.get("metadata", {})
                metadata = json.loads(metadata)

                # Preserve the entire nwp27 object, only updating this key
                nwp27 = metadata.get("nwp27") or {}
                if not isinstance(nwp27, dict):
                    nwp27 = {}
                nwp27[key] = nwp_data
                metadata["nwp27"] = nwp27

                curs.execute("UPDATE events SET metadata = ? WHERE id = ?", (json.dumps(metadata), self.design_id))
                con.commit()
            except Exception:
                con.rollback()
                raise

    def get_project_title(self) -> str:
        """Return the title of the project. Override this method in subclasses."""

        data = self.load_data("projectTitle")
        title = data.get("title", "")
        if title is None or len(title) < 1:
            with DBCon(self.db_path) as con:
                curs = con.cursor()
                curs.execute("SELECT name FROM Events where id = ?", (self.design_id,))
                row = curs.fetchone()
                if row:
                    title = row["name"]

        if title is None or len(title) < 1:
            title = "NWP27 Based on a Riverscapes Studio Design"

        return title

    def get_data_to_save(self) -> dict:
        """Return the data to be saved. Override this method in subclasses."""
        return {}

    def get_package_folder(self) -> str:
        """
        This is the folder inside of which all package files and reports for this design are stored.
        """
        return os.path.join(os.path.dirname(self.db_path), "exports", f"nwp27_package_design_id_{self.design_id}")

    def get_map_layouts_folder(self) -> str:
        """
        This is the folder inside the package folder where map layouts are stored.
        """
        return os.path.join(self.get_package_folder(), "map_layouts")

    def get_reports_folder(self) -> str:
        """
        This is the folder inside the package folder where reports are stored.
        """
        return os.path.join(self.get_package_folder(), "reports")
