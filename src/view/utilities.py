import os
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
    help_url = CONSTANTS['webUrl'].rstrip('/') + '/Software_Help/' + help_slug.strip('/') + '.html' if help_slug is not None and len(help_slug) > 0 else CONSTANTS
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


def add_help_button(form: QtWidgets.QDialog, help_slug: str) -> QtWidgets.QHBoxLayout:

    form.horiz = QtWidgets.QHBoxLayout()

    form.cmdHelp = QtWidgets.QPushButton()
    form.cmdHelp.setText('Help')
    help_url = CONSTANTS['webUrl'].rstrip('/') + '/Software_Help/' + help_slug.strip('/') + '.html' if help_slug is not None and len(help_slug) > 0 else CONSTANTS
    form.cmdHelp.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(help_url)))

    form.horiz.addWidget(form.cmdHelp)

    return form.horiz


def safe_makedirs(dir_create_path):
    """safely, recursively make a directory

    Arguments:
        dir_create_path {[type]} -- [description]
    """

    # Safety check on path lengths
    if len(dir_create_path) < 5 or len(dir_create_path.split(os.path.sep)) <= 2:
        raise Exception('Invalid path: {}'.format(dir_create_path))

    if os.path.exists(dir_create_path) and os.path.isfile(dir_create_path):
        raise Exception('Can\'t create directory if there is a file of the same name: {}'.format(dir_create_path))

    if not os.path.exists(dir_create_path):
        try:
            os.makedirs(dir_create_path)
        except Exception as e:
            # Possible that something else made the folder while we were trying
            if not os.path.exists(dir_create_path):
                raise e
