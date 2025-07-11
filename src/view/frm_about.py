import os
import requests

from PyQt5 import QtCore, QtGui, QtWidgets

from ..QRiS.settings import CONSTANTS

from .. import __version__

html = """
<p>QGIS Riverscapes Studio or QRiS (pronounced curious) is a flagship, professional-grade tool of the <a href="http://riverscapes.net">Riverscapes Consortium</a>. The free, <a href="https://github.com/Riverscapes/QRiS">open-source software</a> is a <a href="https://plugins.qgis.org/">plugin</a> to the free, open-source <a href="https://plugins.qgis.org/">QGIS</a> software. The tool is targeted at anyone interested in understanding and analyzing their riverscape - including:  practitioners, managers, analysts, researchers and students with some familiarity with GIS. It helps users with analysis, monitoring, assessment of riverscapes as well as preparation of the design and as-builts of <a href="http://lowtechpbr.restoration.usu.edu/resources/Topics/04_Design/">low-tech process-based restoration designs</a>. </p>
<h2 id="funding">Funding</h2>
<p>We are grateful to generous grant support from early adopters for the vision behind the Riverscape Studio at the <a href="https://www.blm.gov/programs/aquatics">Bureau of Land Management</a>, the <a href="https://www.fs.usda.gov/detail/r4/landmanagement/resourcemanagement/?cid=stelprd3845865">US Forest Service</a>, <a href="https://www.fisheries.noaa.gov/about/northwest-fisheries-science-center">NOAA Fisheries</a>, <a href="https://www.nrcs.usda.gov/wps/portal/nrcs/detail/national/programs/initiatives/?cid=stelprdb1046975">NRCS Working Lands for Wildlife</a> and <a href="https://anabranchsolutons.com">Anabranch Solutions</a> who funded the professional software development of QRiS.  Without their support, this free software would not exist.</p>

<p>The <a href="https://www.fs.usda.gov/detail/r4/landmanagement/resourcemanagement/?cid=stelprd3845865">US Forest Service</a>, <a href="https://www.fisheries.noaa.gov/about/northwest-fisheries-science-center">NOAA Fisheries</a>, <a href="https://www.nrcs.usda.gov/wps/portal/nrcs/detail/national/programs/initiatives/?cid=stelprdb1046975">NRCS Working Lands for Wildlife</a> and <a href="https://anabranchsolutons.com">Anabranch Solutions</a> were early supporters who paid for development of <a href="https://riverscapes.net/Tools/discrimination.html#tool-grade">proof of concepts</a> and Alpha pre-release versions of the code.  </p>
<p>Specifically, the following supporters and visionaries behind the <a href="http://lowtechpbr.restoration.usu.edu/">Low-Tech Process-Based Restoration</a> made QRiS a reality by raising the funds to develop it.</p>
<ul>
<li><a href="https://www.researchgate.net/profile/Alden-Shallcross">Alden Shalcross</a> (BLM Montana-Dakotas),</li>
<li><a href="https://scholar.google.com/citations?user=JsXtmykAAAAJ&amp;hl=en">Scott Miller</a> (BLM National), </li>
<li><a href="https://www.researchgate.net/profile/Jeremy_Maestas">Jeremy Maestas</a> (NRCS)</li>
<li><a href="https://www.researchgate.net/profile/W-Saunders">Carl Saunders</a>   (US Forest Service)</li>
<li><a href="https://www.researchgate.net/profile/Chris-Jordan-7">Chris Jordan</a> (<a href="https://www.fisheries.noaa.gov/about/northwest-fisheries-science-center">NOAA Fisheries</a>)</li>
<li><a href="https://www.researchgate.net/profile/Nick_Weber2">Nick Weber</a>, <a href="https://www.researchgate.net/profile/Joseph_Wheaton">Joe Wheaton</a>, <a href="https://www.researchgate.net/profile/Stephen_Bennett8">Steve Bennett</a> and <a href="https://www.researchgate.net/profile/Nick_Bouwes">Nick Bouwes</a> (<a href="https://anabranchsolutons.com">Anabranch Solutions</a>)</li>
</ul>
<h2 id="qris-development-team">QRiS Development Team</h2>
<p>QRiS is developed by <a href="http://northarrowresearch.com">North Arrow Research</a>. The QRiS Development Team is led by <a href="https://www.researchgate.net/profile/Philip-Bailey-2">Philip Bailey</a> (Owner of <a href="http://northarrowresearch.com">North Arrow Research</a> and Adjunct Professor at <a href="https://qcnr.usu.edu/wats/">Utah State University</a>),  <a href="http://joewheaton.org">Joseph Wheaton</a> (Professor of Riverscapes at Utah State University) and <a href="https://www.researchgate.net/profile/Nick_Weber2">Nick Weber</a> (<a href="http://anabranchsolutions.com">Anabranch Solutions</a>). The initial plugin was set up by <a href="https://github.com/KellyMWhitehead">Kelly Whitehead</a> and the early releases bringing the LTPBR design functionality were developed by <a href="https://github.com/nick4rivers">Nick Weber</a>. See <a href="https://github.com/Riverscapes/QRiS/graphs/contributors">Contributors on GitHub</a> for the full list of code contributors to QRiS. </p>
"""

class FrmAboutDialog(QtWidgets.QDialog):
    """
    About Dialog
    """

    closingPlugin = QtCore.pyqtSignal()

    def __init__(self, parent):
        """Constructor."""
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi2()

        pixmap = QtGui.QIcon(":/plugins/qris_toolbar/qris_icon").pixmap(128, 128)
        self.logo.setPixmap(pixmap)

        self.setWindowTitle('QRiS Plugin for QGIS')
        self.lblVersion.setText("Version: {}".format(__version__))
        self.lblWebsite.setText('<a href="{0}">{0}</a>'.format(CONSTANTS['webUrl']))
        self.lblIssues.setText('<a href="{0}">{0}</a>'.format(CONSTANTS['issueUrl']))
        self.lblChangelog.setText('<a href="{0}">{0}</a>'.format(CONSTANTS['changelogUrl']))

        # self.acknowledgements = requests.get(CONSTANTS['acknowledgementsUrl']).text
        # self.lblAcknowledgements.setText('<a href="{0}">{0}</a>'.format(CONSTANTS['acknowledgementsUrl']))
        self.lblAcknowledgements.setHtml(html)

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
        # center the logo
        self.logo.setAlignment(QtCore.Qt.AlignCenter)
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
