import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets
from ..QRiS.settings import CONSTANTS


def validate_name(parent: QtWidgets.QWidget, txtName: QtWidgets.QLineEdit) -> bool:

    txtName.setText(txtName.text().strip())
    if len(txtName.text()) < 1:
        QtWidgets.QMessageBox.warning(parent, 'Missing Name', 'You must provide a name to continue.')
        txtName.setFocus()
        return False

    return True


def validate_name_unique(db_path: str, table: str, column: str, value: str) -> bool:

    with sqlite3.connect(db_path) as conn:
        curs = conn.cursor()
        curs.execute(f'SELECT * FROM {table} where {column} like ?', [value])
        return curs.fetchone() is None


def add_standard_form_buttons(form: QtWidgets.QDialog, help_slug: str) -> QtWidgets.QHBoxLayout:

    form.horiz = QtWidgets.QHBoxLayout()

    form.cmdHelp = QtWidgets.QPushButton()
    form.cmdHelp.setText('Help')
    help_url = CONSTANTS['webUrl'] + '/' + help_slug if help_slug is not None and len(help_slug) > 0 else CONSTANTS
    form.cmdHelp.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(help_url)))

    form.horiz.addWidget(form.cmdHelp)

    form.spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
    form.horiz.addItem(form.spacerItem)

    form.buttonBox = QtWidgets.QDialogButtonBox()
    form.horiz.addWidget(form.buttonBox)
    form.buttonBox.setOrientation(QtCore.Qt.Horizontal)
    form.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
    form.buttonBox.accepted.connect(form.accept)
    form.buttonBox.rejected.connect(form.reject)

    return form.horiz
