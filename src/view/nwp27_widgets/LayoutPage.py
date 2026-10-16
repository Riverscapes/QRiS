import os

from qgis.core import QgsProject
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...lib.layout_tools import (
    _get_layout_by_id,
    open_layout,
    print_layout_to_image,
    serialize_layout,
)
from ...QRiS.path_utilities import explore_folder
from .BaseWidget import BaseWidget
from .WizardStatus import PRODUCTS, STEP_COMPLETE, STEP_INCOMPLETE


class LayoutPage(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setTitle("Project Location")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        self.layouts_dir = os.path.join(plugin_root, "resources", "map_templates")

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel(
            "This step produce several maps to support your NWP27 application."
            + " Each map is generated based on a layout template that you can customize around your data."
            + " Click the open buttons beside each map layout below to view and manipulate the layouts using QGIS built-in tools."
            + " When you are finished you must click the print button to preserve your layout changes and also print each layout to PDF and PNG."
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        # Scrollable area for the product rows — populated in refresh_data()
        # once the DB path is known.
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        button_box = QHBoxLayout()
        button_box.addStretch()
        self.layout().addLayout(button_box)

        browse_folder_button = QPushButton()
        browse_folder_button.setFixedWidth(self.BUTTON_WIDTH)
        browse_folder_button.setIcon(QIcon(":plugins/qris_toolbar/folder"))
        browse_folder_button.setToolTip("Browse for the folder containing map layouts.")
        browse_folder_button.clicked.connect(lambda: explore_folder(self.get_map_layouts_folder(), create_if_missing=True))
        button_box.addWidget(browse_folder_button)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        # Tracked so get_status() can evaluate completion without re-creating widgets.
        self._layout_status_keys: list[tuple[str, int | None]] = []

    def refresh_data(self) -> None:
        """(Re)build the layout rows from the database, now that configure() has set db_path."""
        # Clear any previous rows
        self._clear_scroll_layout()
        self._layout_status_keys = []

        # Build a list of all the layouts needed. This is one item for all the project level layouts
        # and then one for each reach level layout
        layout_list = []
        for product in PRODUCTS:
            name = product["name"]
            description = product["description"]
            machine_code = product["machine_code"]
            is_layout = product["is_layout"]

            if is_layout is False:
                continue

            if machine_code.lower() == "nwp_reaches":
                # Repeat this layout for each reach polygon
                reach_info = self.load_reach_info()
                for fid, info in reach_info.items():
                    layout_list.append(
                        {
                            "name": f"{name} - {info['label']}",
                            "description": description,
                            "machine_code": machine_code,
                            "fid": fid,
                        }
                    )
            else:
                layout_list.append({"name": name, "description": description, "machine_code": machine_code, "fid": None})

        for layout_info in layout_list:
            name = layout_info["name"]
            description = layout_info["description"]
            machine_code = layout_info["machine_code"]
            fid = layout_info["fid"]

            self._layout_status_keys.append((machine_code, fid))

            h_layout = QHBoxLayout()
            self.scroll_layout.addLayout(h_layout)

            icon_label = QLabel()
            icon_label.setFixedWidth(16)
            self._update_row_layout_status(icon_label, machine_code, fid)
            h_layout.addWidget(icon_label)

            name_label = QLabel(name)
            name_label.setToolTip(description)
            name_label.setMinimumWidth(160)
            h_layout.addWidget(name_label)

            # description_label = QLabel(description)
            # description_label.setWordWrap(True)
            # h_layout.addWidget(description_label, 1)  # stretch factor 1 — fills remaining space

            # Zoom to feature button
            if fid is not None:
                zoom_button = QPushButton()
                zoom_button.setToolTip("Zoom to this feature in the map")
                zoom_button.setFixedWidth(self.BUTTON_WIDTH)
                zoom_button.setIcon(QIcon(":plugins/qris_toolbar/zoom-in"))
                zoom_button.clicked.connect(lambda _, f=fid: self.zoom_to_feature(f))
                h_layout.addWidget(zoom_button)

            # Open button
            open_button = QPushButton()
            open_button.setToolTip("Open this layout in QGIS layout editor")
            open_button.setFixedWidth(self.BUTTON_WIDTH)
            open_button.setIcon(QIcon(":plugins/qris_toolbar/open"))
            open_button.clicked.connect(lambda _, n=name, c=machine_code, f=fid: self.open_layout(n, c, f))
            h_layout.addWidget(open_button)

            # Save & Print button: serializes the layout to the DB (keyed by
            # machine_code + fid), then exports PDF and PNG to the package folder.
            save_button = QPushButton()
            save_button.setToolTip("Save the layout and print it to PDF and PNG")
            save_button.setFixedWidth(self.BUTTON_WIDTH)
            save_button.setIcon(QIcon(":plugins/qris_toolbar/print"))
            save_button.clicked.connect(lambda _, n=name, c=machine_code, f=fid, icon=icon_label: self.save_and_print_layout(n, c, f, icon))
            h_layout.addWidget(save_button)

            reset_button = QPushButton()
            reset_button.setToolTip("Reset the layout to its original state")
            reset_button.setFixedWidth(self.BUTTON_WIDTH)
            reset_button.setIcon(QIcon(":plugins/qris_toolbar/refresh"))
            reset_button.clicked.connect(lambda _, n=name, c=machine_code, f=fid, icon=icon_label: self.reset_layout(n, c, f, icon))
            h_layout.addWidget(reset_button)

        self.scroll_layout.addStretch()

    def _clear_scroll_layout(self) -> None:
        """Remove all items from the scroll layout."""
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            # Child layouts (QHBoxLayout) — iterate and remove
            child_layout = item.layout()
            if child_layout is not None:
                while child_layout.count() > 0:
                    child_item = child_layout.takeAt(0)
                    child_widget = child_item.widget()
                    if child_widget is not None:
                        child_widget.deleteLater()

    def get_open_layout(self, name: str):
        """
        Retrieve the list of existing layout names in the current QGIS project.
        """

        qgis_project = QgsProject.instance()
        layout_names = [layout.name() for layout in qgis_project.layoutManager().layouts()]
        return layout_names

    def get_status(self) -> int:
        if not self._layout_status_keys:
            return STEP_INCOMPLETE
        for machine_code, fid in self._layout_status_keys:
            png_path = self.get_layout_path(machine_code, "png", fid=fid)
            if not os.path.exists(png_path):
                return STEP_INCOMPLETE
        return STEP_COMPLETE

    def on_text_changed(self):
        self.contentChanged.emit()

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def configure(self, db_path: str, design_id: int) -> None:
        super().configure(db_path, design_id)

    def open_layout(self, name: str, machine_code: str, fid: int | None = None) -> None:

        # Remove any existing layout so it is recreated from the saved XML or template
        layout = _get_layout_by_id(machine_code, False)
        if layout:
            QgsProject.instance().layoutManager().removeLayout(layout)

        storage_key = f"{machine_code}_{fid}" if fid is not None else machine_code

        # Check the database for an existing serialized layout
        existing_layouts = self.load_data("mapLayouts")
        if existing_layouts and storage_key in existing_layouts:
            layout_xml = existing_layouts[storage_key]

            if "{{projectConditions.objectives}}" in layout_xml:
                layout_xml = layout_xml.replace("{{projectConditions.objectives}}", "Fred")

            open_layout(layout_xml, layout_name=machine_code)
            return

        # Fall back to plain machine_code key (project-level)
        if existing_layouts and machine_code in existing_layouts:
            layout_xml = existing_layouts[machine_code]

            if "{{projectConditions.objectives}}" in layout_xml:
                layout_xml = layout_xml.replace("{{projectConditions.objectives}}", "Fred")

            open_layout(layout_xml, layout_name=machine_code)
            return

        # No saved layout exists; open fresh from the QPT template
        layout_path = os.path.join(self.layouts_dir, f"{machine_code}.qpt")
        if os.path.exists(layout_path):
            open_layout(layout_path)

    def save_layout_qml_to_db(self, name: str, machine_code: str, fid: int | None = None) -> str | None:
        """Serialize the layout and save it to the DB keyed by machine_code + fid.

        Returns the storage key on success, or None if the layout was not found.
        """
        layout = _get_layout_by_id(machine_code, False)
        if not layout:
            return None

        current_layout_str = serialize_layout(machine_code)
        if not current_layout_str:
            return None

        storage_key = f"{machine_code}_{fid}" if fid is not None else machine_code

        existing_layouts = self.load_data("mapLayouts")
        if existing_layouts is None:
            existing_layouts = {}

        existing_layouts[storage_key] = current_layout_str
        self._save_data("mapLayouts", existing_layouts)
        return storage_key

    def save_and_print_layout(self, name: str, machine_code: str, fid: int | None = None, icon_label: QLabel | None = None) -> None:
        """Save the layout to the database, then export PDF and PNG to the package folder.

        The layout is stored with a compound key (machine_code + fid) so that
        reach-specific layouts don't overwrite each other or the project-level one.
        After export the row icon is updated to reflect whether the PNG exists on disk.
        """
        storage_key = self.save_layout_qml_to_db(name, machine_code, fid)
        if storage_key is None:
            return

        export_folder = self.get_map_layouts_folder()
        os.makedirs(export_folder, exist_ok=True)

        # print_layout(machine_code, self.get_layout_path(machine_code, "pdf", fid=fid))

        png_path = self.get_layout_path(machine_code, "png", fid=fid)
        print_layout_to_image(machine_code, png_path)

        # Update the row icon based on whether the PNG export succeeded
        self._update_row_layout_status(icon_label, machine_code, fid)

    def _update_row_layout_status(self, icon_label: QLabel | None, machine_code: str, fid: int | None = None) -> None:
        """Update the row icon to check or cancel depending on whether the PNG exists."""
        if icon_label is None:
            return
        png_path = self.get_layout_path(machine_code, "png", fid=fid)
        icon_name = "check" if os.path.exists(png_path) else "cancel"
        icon_label.setPixmap(QIcon(f":/plugins/qris_toolbar/{icon_name}").pixmap(16, 16))

    def zoom_to_feature(self, fid: int | None = None) -> None:
        """Zoom the map canvas to the specified reach feature."""
        if fid is None:
            return
        else:
            self.zoom_to_reach(fid)
