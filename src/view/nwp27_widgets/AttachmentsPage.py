import os

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .BaseWidget import BaseWidget
from .WizardStatus import STEP_UNKNOWN


class AttachmentsPage(BaseWidget):
    contentChanged = pyqtSignal()

    def __init__(self, db_path: str, design_id: str, parent=None):
        super().__init__(db_path, design_id, parent)

        # self.setTitle("Attachments")
        # self.setSubTitle("Please upload any relevant attachments for your project.")

        layout = QVBoxLayout()
        self.setLayout(layout)

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        upload_button = QPushButton("Upload Files")
        upload_button.clicked.connect(self.upload_files)
        button_layout.addWidget(upload_button)

        remove_button = QPushButton("Remove Files")
        remove_button.clicked.connect(self.remove_files)
        button_layout.addWidget(remove_button)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["File Name", "File Path"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def get_status(self) -> int:
        # if self.table.rowCount() > 0:
        #     return 2
        return STEP_UNKNOWN

    def on_text_changed(self):
        self.contentChanged.emit()

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def remove_files(self):
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)
        self.on_text_changed()

    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*);;PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg)")
        if files:
            for file_path in files:
                file_name = os.path.basename(file_path)
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(file_name))
                self.table.setItem(row, 1, QTableWidgetItem(file_path))
            self.on_text_changed()
