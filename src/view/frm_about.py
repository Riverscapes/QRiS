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

    closingPlugin = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi2()

        pixmap = QtGui.QPixmap(':/plugins/qris_toolbar/riverscapes_logo').scaled(128, 128)
        self.logo.setPixmap(pixmap)

        self.setWindowTitle('QRiS Plugin for QGIS')
        self.lblVersion.setText("Version: {}".format(__version__))
        self.lblWebsite.setText('<a href="{0}">{0}</a>'.format(CONSTANTS['webUrl']))
        self.lblIssues.setText('<a href="{0}">{0}</a>'.format(CONSTANTS['issueUrl']))
        self.lblChangelog.setText('<a href="{0}">{0}</a>'.format(CONSTANTS['changelogUrl']))

    def setupUi2(self):

        self.vert = QtWidgets.QVBoxLayout()
        self.setLayout(self.vert)

        self.horiz = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz)

        self.logo = QtWidgets.QLabel()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logo.sizePolicy().hasHeightForWidth())
        self.logo.setSizePolicy(sizePolicy)
        self.logo.setMinimumSize(QtCore.QSize(128, 128))
        self.logo.setMaximumSize(QtCore.QSize(128, 128))
        self.horiz.addWidget(self.logo)

        self.grid = QtWidgets.QGridLayout()
        self.horiz.addLayout(self.grid)

        self.lblVersionHeader = QtWidgets.QLabel()
        self.lblVersionHeader.setText('Version')
        self.grid.addWidget(self.lblVersionHeader, 0, 0, 1, 1)

        self.lblVersion = QtWidgets.QLabel()
        self.grid.addWidget(self.lblVersion, 0, 1, 1, 1)

        self.lblWebSiteHeader = QtWidgets.QLabel()
        self.lblWebSiteHeader.setText('Website')
        self.grid.addWidget(self.lblWebSiteHeader, 1, 0, 1, 1)

        self.lblWebsite = QtWidgets.QLabel()
        self.lblWebsite.setOpenExternalLinks(True)
        self.lblWebsite.setTextFormat(QtCore.Qt.RichText)
        self.grid.addWidget(self.lblWebsite, 1, 1, 1, 1)

        self.lblIssuesHeader = QtWidgets.QLabel()
        self.lblIssuesHeader.setText('Discussions')
        self.grid.addWidget(self.lblIssuesHeader, 2, 0, 1, 1)

        self.lblIssues = QtWidgets.QLabel()
        self.lblIssues.setOpenExternalLinks(True)
        self.lblIssues.setTextFormat(QtCore.Qt.RichText)
        self.grid.addWidget(self.lblIssues, 2, 1, 1, 1)

        self.lblChangelogHeader = QtWidgets.QLabel()
        self.lblChangelogHeader.setText('Changelog')
        self.grid.addWidget(self.lblChangelogHeader, 3, 0, 1, 1)

        self.lblChangelog = QtWidgets.QLabel()
        self.lblChangelog.setOpenExternalLinks(True)
        self.lblChangelog.setTextFormat(QtCore.Qt.RichText)
        self.grid.addWidget(self.lblChangelog, 3, 1, 1, 1)

        self.grpAcknowledgements = QtWidgets.QGroupBox()
        self.grpAcknowledgements.setTitle('Acknowledgements')
        self.vert.addWidget(self.grpAcknowledgements)

        self.lblAcknowledgements = QtWidgets.QTextBrowser(self.grpAcknowledgements)
        self.vert.addWidget(self.lblAcknowledgements)
        self.lblAcknowledgements.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard | QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextBrowserInteraction | QtCore.Qt.TextSelectableByKeyboard | QtCore.Qt.TextSelectableByMouse)
        self.lblAcknowledgements.setOpenExternalLinks(True)

        self.closeButton = QtWidgets.QDialogButtonBox()
        self.closeButton.setOrientation(QtCore.Qt.Horizontal)
        self.closeButton.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.vert.addWidget(self.closeButton)
        self.closeButton.rejected.connect(self.reject)
        self.closeButton.accepted.connect(self.accept)
