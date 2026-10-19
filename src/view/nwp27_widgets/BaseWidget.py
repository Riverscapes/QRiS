from abc import abstractmethod
import json
import os

from qgis.core import QgsCoordinateTransform, QgsProject
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

    # Cache the parsed NWP27 metadata dict so that all pages share a single
    # DB round-trip + JSON parse during initialization.  Keyed by
    # (db_path, design_id); invalidated on _save_data().
    _nwp_metadata_cache: dict[tuple[str, int], dict] = {}

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

    def _load_nwp_metadata(self) -> dict:
        """Return the parsed ``nwp27`` dict from the event metadata, using a class-level cache.

        The cache key is ``(db_path, design_id)`` so that switching between
        projects or events invalidates automatically.  Callers that mutate the
        metadata must call :meth:`_invalidate_nwp_cache` afterwards.
        """
        key = (self.db_path, self.design_id)
        if key not in self._nwp_metadata_cache:
            with DBCon(self.db_path) as con:
                curs = con.cursor()
                curs.execute("SELECT metadata as info FROM events WHERE id = ?", (self.design_id,))
                row = curs.fetchone()
                if not row:
                    return {}
                raw = row.get("info")
                if isinstance(raw, str):
                    parsed = json.loads(raw)
                    self._nwp_metadata_cache[key] = parsed.get("nwp27") if isinstance(parsed, dict) else {}
                else:
                    self._nwp_metadata_cache[key] = {}
        return self._nwp_metadata_cache[key]

    def _invalidate_nwp_cache(self) -> None:
        """Remove the cached NWP27 metadata for this widget's project/event."""
        self._nwp_metadata_cache.pop((self.db_path, self.design_id), None)

    def load_data(self, key: str) -> dict:
        nwp27 = self._load_nwp_metadata()
        return nwp27.get(key, {}) if isinstance(nwp27, dict) else {}

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

        # Invalidate the cache so subsequent reads pick up the new data
        self._invalidate_nwp_cache()

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

    def get_reaches_layer(self) -> int:
        layer_data = self.load_data("locations")
        if layer_data:
            reaches_data = layer_data.get("reaches")
            if reaches_data:
                # Return the first reach as a placeholder
                return reaches_data
        return 0

    def load_reach_info(self) -> dict:

        reaches_id = self.get_reaches_layer()
        if reaches_id < 1:
            return

        reach_info = {}
        with DBCon(self.db_path) as con:
            curs = con.cursor()
            curs.execute("SELECT fid, coalesce(display_label, fid) as label FROM sample_frame_features WHERE sample_frame_id = ?", (reaches_id,))
            for row in curs.fetchall():
                reach_info[row["fid"]] = {"fid": row["fid"], "label": row["label"]}

        return reach_info

    def zoom_to_reach(self, fid: int) -> None:
        """Zoom to the specified reach feature in the map."""

        reaches_id = self.get_reaches_layer()
        if reaches_id < 1:
            return

        # Add the reaches sample frame layer to the map if it is not already there
        layer = self.add_to_map("reaches")
        if layer is None:
            return

        # Zoom to the reach feature
        feature = layer.getFeature(fid)
        if not feature.isValid() or feature.geometry().isEmpty():
            return

        canvas = Settings().iface.mapCanvas()
        if layer.crs() != canvas.mapSettings().destinationCrs():
            transform = QgsCoordinateTransform(layer.crs(), canvas.mapSettings().destinationCrs(), QgsProject.instance())
            extent = transform.transformBoundingBox(feature.geometry().boundingBox())
        else:
            extent = feature.geometry().boundingBox()

        # Expand slightly to prevent a tight fit
        extent.scale(1.1)
        canvas.setExtent(extent)
        canvas.refresh()

    def get_layout_path(self, machine_code: str, extension: str, fid: int | None = None) -> str:
        """Return the file path for the layout PDF based on machine_code and optional fid."""
        safe_name = machine_code.replace(" ", "_").replace("(", "").replace(")", "")
        if fid is not None:
            safe_name = f"{safe_name}_reach_{fid}"
        export_folder = self.get_map_layouts_folder()
        return os.path.join(export_folder, f"{safe_name}.{extension}")
