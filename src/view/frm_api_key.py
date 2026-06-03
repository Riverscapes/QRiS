from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QApplication, QDialog, QVBoxLayout,
                                  QLabel, QDialogButtonBox)
from qgis.gui import QgsPasswordLineEdit

from ..lib.climate_engine import CLIMATE_ENGINE_API_KEY_SETTING, check_climate_engine_api_key
from ..QRiS.settings import Settings


class FrmApiKey(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Climate Engine API Key")
        self.setMinimumWidth(460)
        self.setMaximumHeight(200)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        lbl = QLabel("Enter your Climate Engine API key. The key will be validated when you click OK.")
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.PlainText)
        layout.addWidget(lbl)

        self.txt_api_key = QgsPasswordLineEdit()
        self.txt_api_key.setPlaceholderText("Paste your API key here…")
        self.txt_api_key.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.txt_api_key)

        self.lbl_status = QLabel()
        self.lbl_status.setTextFormat(Qt.RichText)
        self.lbl_status.setMinimumHeight(self.lbl_status.sizeHint().height())
        layout.addWidget(self.lbl_status)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        layout.addWidget(self.button_box)

    def _on_text_changed(self):
        self.lbl_status.setText('')
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(bool(self.txt_api_key.text().strip()))

    def _on_accept(self):
        api_key = self.txt_api_key.text().strip()
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.lbl_status.setText('Validating\u2026')
        QApplication.processEvents()

        valid = check_climate_engine_api_key(api_key)

        if valid:
            Settings().setSecureValue(CLIMATE_ENGINE_API_KEY_SETTING, api_key)
            super().accept()
        else:
            self.lbl_status.setText('<span style="color:red; font-size:14px;">&#10008; Invalid key. Please check and try again.</span>')
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
