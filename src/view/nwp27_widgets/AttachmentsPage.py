from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ...compat import USER_ROLE
from ...model.attachment import Attachment
from ...model.project import Project
from ...view.frm_attachment import FrmAttachment
from .BaseWidget import BaseWidget
from .WizardStatus import STEP_UNKNOWN


class AttachmentsPage(BaseWidget):
    contentChanged = pyqtSignal()
    attachments_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        upload_button = QPushButton("Add New File Attachment")
        upload_button.clicked.connect(self.upload_files)
        button_layout.addWidget(upload_button)

        remove_button = QPushButton("Remove File Attachment")
        remove_button.clicked.connect(self.remove_files)
        button_layout.addWidget(remove_button)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["File Name", "File Path", "Type"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.on_table_double_clicked)
        layout.addWidget(self.table)

        self._project = None

    def set_project(self, project: Project):
        """Set the shared Project instance (from the dock widget) so changes are reflected in the tree."""
        self._project = project

    def configure(self, db_path: str, design_id: int) -> None:
        super().configure(db_path, design_id)

    def get_status(self) -> int:
        return STEP_UNKNOWN

    def on_text_changed(self):
        self.contentChanged.emit()

    def deserialize(self, data: dict) -> None:
        pass

    def serialize(self) -> None:
        pass

    def refresh_data(self):
        """Reload the table from the project's nwp27-tagged attachments."""
        if self._project is None:
            return
        self.table.setRowCount(0)
        for attachment in self._project.attachments.values():
            meta = attachment.metadata or {}
            if meta.get("metadata", {}).get("nwp27"):
                row = self.table.rowCount()
                self.table.insertRow(row)
                name_item = QTableWidgetItem(attachment.name)
                name_item.setData(USER_ROLE, attachment.id)
                self.table.setItem(row, 0, name_item)
                self.table.setItem(row, 1, QTableWidgetItem(attachment.path))
                self.table.setItem(row, 2, QTableWidgetItem(attachment.attachment_type))

    def remove_files(self):
        if self._project is None:
            return

        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        if not selected_rows:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete the selected attachment(s)?\n\nThis will remove the attachment from the project and delete the file from disk.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for row in sorted(selected_rows, reverse=True):
            name_item = self.table.item(row, 0)
            if name_item is None:
                continue
            attachment_id = name_item.data(USER_ROLE)
            attachment = self._project.attachments.get(attachment_id)
            if attachment is not None:
                attachment.delete(self.db_path)
                self._project.attachments.pop(attachment_id, None)
            self.table.removeRow(row)

        self.on_text_changed()
        self.attachments_changed.emit()

    def on_table_double_clicked(self, row: int, column: int):
        """Open the FrmAttachment dialog in edit mode for the double-clicked attachment."""
        if self._project is None:
            return
        name_item = self.table.item(row, 0)
        if name_item is None:
            return
        attachment_id = name_item.data(USER_ROLE)
        attachment = self._project.attachments.get(attachment_id)
        if attachment is None:
            return
        frm = FrmAttachment(self, self._project, attachment=attachment)
        frm.exec()
        self.refresh_data()
        self.on_text_changed()
        self.attachments_changed.emit()

    def upload_files(self):
        if self._project is None:
            return

        initial_metadata = {"metadata": {"nwp27": "true"}}
        frm = FrmAttachment(self, self._project, attachment_type=Attachment.TYPE_FILE, initial_metadata=initial_metadata)
        frm.exec()
        self.refresh_data()
        self.on_text_changed()
        self.attachments_changed.emit()
