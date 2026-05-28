from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                                  QLabel, QPushButton, QDialogButtonBox)
from qgis.gui import QgsPasswordLineEdit

from ..lib.climate_engine import CLIMATE_ENGINE_API_KEY_SETTING, check_climate_engine_api_key
from ..QRiS.settings import Settings


class FrmApiKey(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Climate Engine API Key")
        self.setMinimumWidth(460)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        lbl = QLabel("Enter your Climate Engine API key. Click <b>Validate</b> to verify it before saving.")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        horiz_key = QHBoxLayout()
        layout.addLayout(horiz_key)

        self.txt_api_key = QgsPasswordLineEdit()
        self.txt_api_key.setPlaceholderText("Paste your API key here…")
        self.txt_api_key.textChanged.connect(self._on_text_changed)
        horiz_key.addWidget(self.txt_api_key)

        self.btn_validate = QPushButton("Validate")
        self.btn_validate.setEnabled(False)
        self.btn_validate.clicked.connect(self._validate)
        horiz_key.addWidget(self.btn_validate)

        self.lbl_status = QLabel()
        self.lbl_status.setTextFormat(Qt.RichText)
        self.lbl_status.setMinimumHeight(self.lbl_status.sizeHint().height())
        layout.addWidget(self.lbl_status)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        layout.addWidget(self.button_box)

    def _on_text_changed(self):
        self.btn_validate.setEnabled(bool(self.txt_api_key.text().strip()))
        self.lbl_status.setText('')
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def _validate(self):
        api_key = self.txt_api_key.text().strip()
        self.btn_validate.setEnabled(False)
        self.lbl_status.setText('Validating\u2026')
        QApplication.processEvents()

        valid = check_climate_engine_api_key(api_key)

        self.btn_validate.setEnabled(True)
        if valid:
            self.lbl_status.setText('<span style="color:green; font-size:14px;">&#10004; Valid</span>')
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.lbl_status.setText('<span style="color:red; font-size:14px;">&#10008; Invalid key</span>')
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def accept(self):
        Settings().setSecureValue(CLIMATE_ENGINE_API_KEY_SETTING, self.txt_api_key.text().strip())
        super().accept()
