import requests
from PyQt5 import QtCore, QtGui, QtWidgets

from ..QRiS.settings import CONSTANTS

from .. import __version__


class FrmAboutDialog(QtWidgets.QDialog):
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

        # self.lblAcknowledgements.setHtml("""<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
        #     "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        #     "p, li { white-space: pre-wrap; }\n"
        #     "</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
        #     "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        # """)

        self.acknowledgements = requests.get(CONSTANTS['acknowledgementsUrl']).text
        self.lblAcknowledgements.setHtml(self.acknowledgements)

    def setupUi2(self):

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
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
        self.lblAcknowledgements.setEnabled(True)
        self.lblAcknowledgements.setReadOnly(True)
        self.lblAcknowledgements.setCursorWidth(0)
        self.lblAcknowledgements.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard | QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextBrowserInteraction | QtCore.Qt.TextSelectableByKeyboard | QtCore.Qt.TextSelectableByMouse)
        self.lblAcknowledgements.setObjectName('acknowledgements')
        self.lblAcknowledgements.setOpenExternalLinks(True)
        self.vert.addWidget(self.lblAcknowledgements)

        self.closeButton = QtWidgets.QDialogButtonBox()
        self.closeButton.setOrientation(QtCore.Qt.Horizontal)
        self.closeButton.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.vert.addWidget(self.closeButton)
        self.closeButton.rejected.connect(self.reject)
        self.closeButton.accepted.connect(self.accept)
