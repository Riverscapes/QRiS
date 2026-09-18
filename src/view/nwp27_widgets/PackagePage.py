import json
import os

from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .BaseWidget import BaseWidget
from .DBCon import DBCon
from .WizardStatus import STEP_UNKNOWN

PRODUCTS = [
    "JSON Export",
    "json_export",
    "product B name",
    "callback_B",
    "product C name",
    "callback_C",
]


class PackagePage(BaseWidget):
    def __init__(self, db_path: str, design_id: str, parent=None):
        super().__init__(db_path, design_id, parent)

        self.export_folder = os.path.join(os.path.dirname(self.db_path), "exports", "nwp27_package")

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Introductory text label above the table
        intro_label = QLabel("This step generates output products for the Nationwide Permit 27 application. Select the products you wish to generate below and click 'Produce Checked Products'.")
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)

        # Top layout for buttons, aligned to the right
        top_button_layout = QHBoxLayout()
        top_button_layout.addStretch()

        check_all_btn = QPushButton("Check All")
        check_all_btn.clicked.connect(self.check_all_products)
        top_button_layout.addWidget(check_all_btn)

        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all_products)
        top_button_layout.addWidget(clear_all_btn)

        layout.addLayout(top_button_layout)

        # Table listing the products
        self.table = QTableWidget(0, 2)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 30)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Populate table with default-checked product items
        product_pairs = list(zip(PRODUCTS[0::2], PRODUCTS[1::2]))
        self._product_callbacks = {}
        for name, callback in product_pairs:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Checkbox in 1st column checked by default
            chk = QCheckBox()
            chk.setChecked(True)
            chk.stateChanged.connect(self.on_text_changed)
            self.table.setCellWidget(row, 0, chk)
            self._product_callbacks[row] = callback

            # Product name in 2nd column
            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 1, name_item)

        layout.addWidget(self.table)

        # Produce Checked Products button below the table
        produce_btn = QPushButton("Produce Checked Products")
        produce_btn.clicked.connect(self.produce_products)
        layout.addWidget(produce_btn)

    def get_status(self) -> int:
        # Packaging has no logic. Simply show grey icon
        return STEP_UNKNOWN

    def on_text_changed(self):
        self.contentChanged.emit()

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def check_all_products(self) -> None:
        """Check all product checkboxes in the table."""
        for row in range(self.table.rowCount()):
            chk = self.table.cellWidget(row, 0)
            if isinstance(chk, QCheckBox):
                chk.setChecked(True)
        self.on_text_changed()

    def clear_all_products(self) -> None:
        """Clear all product checkboxes in the table."""
        for row in range(self.table.rowCount()):
            chk = self.table.cellWidget(row, 0)
            if isinstance(chk, QCheckBox):
                chk.setChecked(False)
        self.on_text_changed()

    def produce_products(self) -> None:
        """Calls all the callback functions associated with each checked product."""

        export_count = 0
        for row in range(self.table.rowCount()):
            chk = self.table.cellWidget(row, 0)
            if isinstance(chk, QCheckBox) and chk.isChecked():
                callback_name = self._product_callbacks[row]
                callback_func = getattr(self, callback_name, None)
                if callback_func and callable(callback_func):
                    callback_func()
                    export_count += 1
                else:
                    print(f"Callback {callback_name} is not implemented or not callable.")

        if export_count > 0:
            # Show a message box offering to browse the folder

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText("NWP package products exported successfully.")
            msg_box.setInformativeText("Do you want to browse the export folder?")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            ret = msg_box.exec()
            if ret == QMessageBox.StandardButton.Yes:
                import subprocess
                import sys

                if sys.platform == "darwin":
                    subprocess.Popen(["open", self.export_folder])
                elif sys.platform == "win32":
                    subprocess.Popen(["explorer", self.export_folder])
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

                # Write the metadata to the output path
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w") as f:
                    json.dump(nwp_data, f, indent=4)

    def callback_B(self) -> None:
        print("callback_B called")

    def callback_C(self) -> None:
        print("callback_C called")
