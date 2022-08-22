from qgis.PyQt.QtWidgets import QMessageBox, QDialog
from ..model.project import Project
from .ui.pour_point import Ui_PoutPoint


class FrmPourPoint(QDialog, Ui_PoutPoint):

    def __init__(self, parent, latitude, longitude):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle('Create New Pour Point with Catchment')

        self.txtLatitude.setText(str(latitude))
        self.txtLongitude.setText(str(longitude))

        self.txtLatitude.setReadOnly(True)
        self.txtLongitude.setReadOnly(True)

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Name', 'You must provide a pour point name to continue.')
            self.txtName.setFocus()
            return()

        super().accept()
