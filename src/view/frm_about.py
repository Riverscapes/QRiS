from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtCore import pyqtSignal

from ..QRiS.settings import CONSTANTS

from .ui.about_dialog import Ui_Dialog

from .. import __version__


class FrmAboutDialog(QDialog, Ui_Dialog):
    """
    About Dialog
    """

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        QDialog.__init__(self, parent)
        self.setupUi(self)

        pixmap = QPixmap(':/plugins/qris_toolbar/RaveAddIn.png').scaled(128, 128)
        self.logo.setPixmap(pixmap)
        self.website.setText('<a href="{0}">{0}</a>'.format(CONSTANTS['webUrl']))
        self.issues.setText('<a href="{0}">{0}</a>'.format(CONSTANTS['issueUrl']))
        self.changelog.setText('<a href="{0}">{0}</a>'.format(CONSTANTS['changelogUrl']))

        self.version.setText("Version: {}".format(__version__))
