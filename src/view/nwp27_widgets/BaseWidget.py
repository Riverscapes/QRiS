from abc import abstractmethod
import json

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QPlainTextEdit, QWidget

from .DBCon import DBCon


class BaseWidget(QWidget):
    contentChanged = pyqtSignal()

    LINE_EDIT_MAX_LENGTH = 255
    TEXT_EDIT_MAX_LENGTH = 1024

    BUTTON_WIDTH = 32

    def __init__(self, db_path: str, design_id: int, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.design_id = design_id

        # Give QLineEdit a visible border (QTextEdit has one by default)
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                padding: 2px 4px;
            }
        """)

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

    def get_data_to_save(self) -> dict:
        """Return the data to be saved. Override this method in subclasses."""
        return {}
