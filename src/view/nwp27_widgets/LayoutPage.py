import os

from qgis.core import QgsProject
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ...lib.layout_tools import (
    _get_layout_by_id,
    open_layout,
    print_layout,
    serialize_layout,
)
from .BaseWidget import BaseWidget
from .WizardStatus import PRODUCTS, STEP_UNKNOWN


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
            "This step builds several maps that support your NWP27 application."
            + " Each map is generated based on a specific layout template."
            + " Click the open buttons to view each of the layouts and manipulate them using QGIS native layout tools."
            + " When you are finished you must click the save button to preserve your changes."
            + " You can print the layouts at this step, or wait and print them during the final package step at the end of the NWP27 process.\n\n"
            + "You must click the save button. Closing the layout editor without clicking the save button below will lose your changes.\n"
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        for product in PRODUCTS:
            name = product["name"]
            description = product["description"]
            machine_code = product["machine_code"]
            is_layout = product["is_layout"]

            if not is_layout:
                continue

            h_layout = QHBoxLayout()
            layout.addLayout(h_layout)

            name_label = QLabel(name)
            h_layout.addWidget(name_label)

            description_label = QLabel(description)
            description_label.setWordWrap(True)
            h_layout.addWidget(description_label)

            # add three buttons for opening, saving and printing each layout
            open_button = QPushButton()
            open_button.setToolTip("Open")
            open_button.setFixedWidth(self.BUTTON_WIDTH)
            open_button.setIcon(QIcon(":plugins/qris_toolbar/open"))
            open_button.clicked.connect(lambda _, name=name, code=machine_code: self.open_layout(name, code))
            h_layout.addWidget(open_button)

            save_button = QPushButton()
            save_button.setToolTip("Save")
            save_button.setFixedWidth(self.BUTTON_WIDTH)
            save_button.setIcon(QIcon(":plugins/qris_toolbar/save"))
            save_button.clicked.connect(lambda _, name=name, code=machine_code: self.save_layout(name, code))
            h_layout.addWidget(save_button)

            print_button = QPushButton()
            print_button.setToolTip("Print")
            print_button.setFixedWidth(self.BUTTON_WIDTH)
            print_button.setIcon(QIcon(":plugins/qris_toolbar/print"))
            print_button.clicked.connect(lambda _, name=name, code=machine_code: self.print_layout(name, code))
            h_layout.addWidget(print_button)

        # stretch
        layout.addStretch()

    def get_open_layout(self, name: str):
        """
        Retrieve the list of existing layout names in the current QGIS project.
        """

        qgis_project = QgsProject.instance()
        layout_names = [layout.name() for layout in qgis_project.layoutManager().layouts()]
        return layout_names

    def get_status(self) -> int:
        return STEP_UNKNOWN

    def on_text_changed(self):
        self.contentChanged.emit()

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def configure(self, db_path: str, design_id: int) -> None:
        super().configure(db_path, design_id)

    def open_layout(self, name: str, machine_code: str) -> None:

        # Remove any existing layout so it is recreated from the saved XML or template
        layout = _get_layout_by_id(machine_code, False)
        if layout:
            # Settings().iface.openLayoutDesigner(layout)
            # return
            QgsProject.instance().layoutManager().removeLayout(layout)

        # Check the database for an existing serialized layout
        existing_layouts = self.load_data("mapLayouts")
        if existing_layouts and machine_code in existing_layouts:
            # Load from saved XML
            layout_xml = existing_layouts[machine_code]

            if "{{projectConditions.objectives}}" in layout_xml:
                layout_xml = layout_xml.replace("{{projectConditions.objectives}}", "Fred")

            open_layout(layout_xml, layout_name=machine_code)
            return

        # No saved layout exists; open fresh from the QPT template
        layout_path = os.path.join(self.layouts_dir, f"{machine_code}.qpt")
        if os.path.exists(layout_path):
            open_layout(layout_path)

    def save_layout(self, name: str, machine_code: str) -> None:

        # Get the layout from the QGIS project by its machine code name
        layout = _get_layout_by_id(machine_code, False)
        if not layout:
            return

        # Serialize the current state of the layout in the designer to XML
        current_layout_str = serialize_layout(machine_code)
        if not current_layout_str:
            return

        existing_layouts = self.load_data("mapLayouts")
        if existing_layouts is None:
            existing_layouts = {}

        existing_layouts[machine_code] = current_layout_str

        self._save_data("mapLayouts", existing_layouts)

    def print_layout(self, name: str, machine_code: str) -> None:
        """Export the layout to a PDF in the package folder and open it in the default viewer."""
        # Ensure the layout is loaded into the project silently
        if not _get_layout_by_id(machine_code, False):
            existing_layouts = self.load_data("mapLayouts")
            if existing_layouts and machine_code in existing_layouts:
                open_layout(existing_layouts[machine_code], layout_name=machine_code, show_designer=False)
            else:
                layout_path = os.path.join(self.layouts_dir, f"{machine_code}.qpt")
                if not os.path.exists(layout_path):
                    return
                open_layout(layout_path, show_designer=False)

        # Print to PDF in the package folder
        safe_name = machine_code.replace(" ", "_").replace("(", "").replace(")", "")

        export_folder = self.get_map_layouts_folder()
        os.makedirs(export_folder, exist_ok=True)

        out_path = os.path.join(export_folder, f"{safe_name}.pdf")
        print_layout(machine_code, out_path)

        # Open the PDF in the system's default viewer
        if os.path.exists(out_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(out_path))
