import json
import os
import subprocess
import sys

from jinja2 import Environment, FileSystemLoader, select_autoescape
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ...gp.vicinity_map import VicinityMapExportTask
from ...lib.layout_tools import _get_layout_by_id, open_layout, print_layout, print_layout_to_image
from .BaseWidget import BaseWidget
from .DBCon import DBCon
from .WizardStatus import PRODUCTS, STEP_UNKNOWN

"""Default keys and helper functions for NWP 27 data.
If these are missing then Jinja substitution will raise an UndefinedError.
The following will fail because the "or" check only looks at the last element.

<tr><th>Project Title</th><td>{{ data.projectTitle.title or "" }}</td></tr>
"""
_NWP_DEFAULT_KEYS = {
    "projectTitle",
    "permittee",
    "projectConditions",
    "esaRelevance",
    "historicProperties",
    "waterQuality",
    "wildScenicRivers",
    "adaptiveManagementPlan",
    "monitoringAndReporting",
    "reaches",
}


def _ensure_nwp_defaults(nwp_data: dict) -> None:
    """Fill in any top-level keys the template expects that are missing from nwp_data.

    Jinja2 raises ``UndefinedError`` when you access ``data.missingKey`` on a dict
    even if the expression has an ``or ""`` fallback, because ``getattr`` is called
    before the ``or`` is evaluated.  This helper ensures every expected key exists
    (defaulting to an empty dict or list as appropriate) so the template renders
    without error.
    """
    for key in _NWP_DEFAULT_KEYS:
        if key not in nwp_data:
            nwp_data[key] = {}


class PackagePage(BaseWidget):
    productsExportedSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.export_folder = None
        self._project = None
        self._vicinity_map_info = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Introductory text label above the table
        intro_label = QLabel("This step generates output products for the Nationwide Permit 27 application. The following products will be packaged into the exports folder for this QRiS project:")
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)

        layout.addSpacing(20)

        # Table listing the products
        self.table = QTableWidget(0, 1)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Populate table with the product items
        for product in PRODUCTS:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Product name in 1st column
            name_item = QTableWidgetItem(product["name"])
            self.table.setItem(row, 0, name_item)

        layout.addWidget(self.table)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        # Produce Products button below the table
        produce_btn = QPushButton("Generate Products")
        produce_btn.clicked.connect(self.generate_products)
        hbox.addWidget(produce_btn)

        browse_btn = QPushButton("Browse Package Folder")
        browse_btn.clicked.connect(self.browse_export_folder)
        hbox.addWidget(browse_btn)

    def set_project(self, project) -> None:
        self._project = project

    def configure(self, db_path: str, design_id: int) -> None:
        super().configure(db_path, design_id)
        self.export_folder = self.get_package_folder()

    def get_status(self) -> int:
        # Packaging has no logic. Simply show grey icon
        return STEP_UNKNOWN

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def _export_layout(self, product: dict) -> None:
        """Ensure the layout is in the project (without opening the designer), then print it to PDF."""
        machine_code = product["machine_code"]
        name = product["name"]

        # Ensure the layout is loaded into the project silently
        layout = _get_layout_by_id(machine_code, False)
        if not layout:
            existing_layouts = self.load_data("mapLayouts")
            if existing_layouts and machine_code in existing_layouts:
                layout_xml = existing_layouts[machine_code]
                open_layout(layout_xml, layout_name=machine_code, show_designer=False)
            else:
                # Load from template
                current_dir = os.path.dirname(os.path.abspath(__file__))
                plugin_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
                layout_path = os.path.join(plugin_root, "resources", "map_templates", f"{machine_code}.qpt")
                if os.path.exists(layout_path):
                    open_layout(layout_path, show_designer=False)
                else:
                    print(f"Layout template not found for '{name}'")
                    return

        # Print to PDF
        safe_name = machine_code.replace(" ", "_").replace("(", "").replace(")", "")
        out_path = os.path.join(self.get_map_layouts_folder(), f"{safe_name}.pdf")
        print_layout(machine_code, out_path)

        output_path = os.path.join(self.get_map_layouts_folder(), f"{safe_name}.png")
        print_layout_to_image(machine_code, output_path)

    def generate_products(self) -> None:
        """Produce all the products."""

        export_count = 0
        for product in PRODUCTS:
            if product["is_layout"]:
                # Print the layout to a PDF
                self._export_layout(product)
                export_count += 1
            else:
                callback_name = product["machine_code"]
                callback_func = getattr(self, callback_name, None)
                if callback_func and callable(callback_func):
                    callback_func()
                    export_count += 1
                else:
                    print(f"Callback {callback_name} is not implemented or not callable.")

        if export_count > 0:
            self.productsExportedSignal.emit()
            # Show a message box offering to browse the folder

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText("NWP package products exported successfully.")
            msg_box.setInformativeText("Do you want to browse the export folder?")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            ret = msg_box.exec()
            if ret == QMessageBox.StandardButton.Yes:
                if sys.platform == "darwin":
                    subprocess.Popen(["open", self.export_folder])
                elif sys.platform == "win32":
                    os.startfile(os.path.normpath(self.export_folder))
                else:
                    subprocess.Popen(["xdg-open", self.export_folder])

    # Stub callbacks associated with each product

    def json_export(self) -> None:

        output_path = os.path.join(self.export_folder, "project.json")

        with DBCon(self.db_path) as con:
            curs = con.cursor()
            curs.execute("SELECT metadata FROM events WHERE id = ?", (self.design_id,))
            metadata = curs.fetchone()["metadata"]
            if metadata:
                metadata = json.loads(metadata)
                nwp_data = metadata.get("nwp27", {})

                # Remove any keys called 'mapLayouts'
                nwp_data.pop("mapLayouts", None)

                # Write the metadata to the output path
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w") as f:
                    json.dump(nwp_data, f, indent=4)

    def html_export(self) -> None:
        """Render the NWP 27 project data to an HTML file using the Jinja2 template."""
        output_path = os.path.join(self.export_folder, "nwp27_document.html")

        with DBCon(self.db_path) as con:
            curs = con.cursor()
            curs.execute("SELECT metadata FROM events WHERE id = ?", (self.design_id,))
            metadata = curs.fetchone()["metadata"]
            if not metadata:
                return
            metadata = json.loads(metadata)
            nwp_data = metadata.get("nwp27", {})

            # Remove any keys called 'mapLayouts'
            nwp_data.pop("mapLayouts", None)

            # Ensure the stream name is included in the NWP data
            nwp_data["streamName"] = nwp_data.get("streamName", "")

        # Reference the Vicinity Map PNG if it was produced
        vicinity_map = next((p for p in PRODUCTS if p["name"] == "Vicinity Map"), None)
        if vicinity_map:
            safe_name = vicinity_map["machine_code"].replace(" ", "_").replace("(", "").replace(")", "")
            png_name = f"{safe_name}.png"
            if os.path.exists(os.path.join(self.export_folder, png_name)):
                nwp_data["vicinityMapLayout"] = png_name
                if self._vicinity_map_info:
                    nwp_data["vicinityRegionLabel"] = self._vicinity_map_info["region_label"]
                    nwp_data["vicinityLatitude"] = self._vicinity_map_info["latitude"]
                    nwp_data["vicinityLongitude"] = self._vicinity_map_info["longitude"]

        # Reference the Project Elements layout PNG if it was produced,
        # so the template can embed it (the HTML is in the same folder).
        project_elements = next((p for p in PRODUCTS if p["is_layout"] and p["name"] == "Project Elements Layout"), None)
        if project_elements:
            safe_name = project_elements["machine_code"].replace(" ", "_").replace("(", "").replace(")", "")
            png_name = f"{safe_name}.png"
            if os.path.exists(os.path.join(self.export_folder, png_name)):
                nwp_data["projectElementsLayout"] = png_name

        # Ensure all top-level keys the template expects exist, so Jinja2
        # doesn't raise UndefinedError when a key is missing from the dict.
        _ensure_nwp_defaults(nwp_data)

        # Locate the Jinja2 template in the plugin's resources folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        template_dir = os.path.join(plugin_root, "resources")

        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template("nwp27_template.html")
        html = template.render(data=nwp_data)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    def nwp27_document(self) -> None:
        output_path = os.path.join(self.export_folder, "nwp27_document.docx")

        # Implement the logic to generate the NWP 27 Word document here
        # For now, just create an empty file as a placeholder
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write("")

    def vicinity_map(self) -> str:
        """Run the vicinity map export geoprocessing task and save a PNG into the export folder."""
        if self._project is None:
            QMessageBox.warning(self, "Vicinity Map", "The QRiS project is not loaded, so the vicinity map cannot be generated.")
            return ""

        os.makedirs(self.export_folder, exist_ok=True)
        output_path = os.path.join(self.export_folder, "vicinity_map.png")

        task = VicinityMapExportTask(output_path, self._project)
        QgsApplication.taskManager().addTask(task)
        task.waitForFinished()

        if task.exception is not None or not os.path.exists(output_path):
            QMessageBox.warning(self, "Vicinity Map", f"Failed to generate the vicinity map: {task.exception}")
            return ""

        # Store the task results for use by the HTML export
        self._vicinity_map_info = {
            "png": os.path.basename(output_path),
            "region_label": task.region_label or "",
            "latitude": f"{task.centroid.y():.6f}" if task.centroid else "",
            "longitude": f"{task.centroid.x():.6f}" if task.centroid else "",
        }
        return os.path.basename(output_path)

    def browse_export_folder(self) -> None:
        """Open Finder / Windows Explorer at the export/package folder."""

        if not self.export_folder:
            return
        if not os.path.exists(self.export_folder):
            os.makedirs(self.export_folder, exist_ok=True)

        if sys.platform == "darwin":
            subprocess.Popen(["open", self.export_folder])
        elif sys.platform == "win32":
            # Use os.startfile on Windows — it handles spaces and mixed slashes
            # without blocking, and doesn't depend on explorer.exe being in PATH.
            os.startfile(os.path.normpath(self.export_folder))
        else:
            subprocess.Popen(["xdg-open", self.export_folder])
