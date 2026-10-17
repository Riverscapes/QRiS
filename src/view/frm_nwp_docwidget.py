"""
/***************************************************************************
 FrmNwpDocWidget
                                 A QGIS plugin
 QGIS Riverscapes Studio (QRiS)
                             -------------------
        begin                : 2026-09-18
        copyright            : (C) 2026 by North Arrow Research
        email                : info@northarrowresearch.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt import QtCore, QtWidgets

from ..compat import DOCK_CLOSABLE, DOCK_FLOATABLE, DOCK_MOVABLE
from ..model.event import Event
from ..model.project import Project
from ..view.nwp27_widgets.MainWidget import MainWidget


class FrmNwpDocWidget(QtWidgets.QDockWidget):
    closing = QtCore.pyqtSignal()

    def __init__(self, parent, iface):

        super().__init__(parent)
        self.iface = iface
        self.setFeatures(DOCK_CLOSABLE | DOCK_MOVABLE | DOCK_FLOATABLE)
        self.connections = {}
        self.setupUi()
        self.resize(500, 800)

        self.destroyed.connect(self.cleanup_connections)

    def configure(self, project: Project, event: Event):
        self.qris_project = project
        self.event = event
        self.setWindowTitle(f"NWP Package - {event.name}")
        self.nwp_widget.configure(project.project_file, event.id, project=project)

    def setupUi(self):

        self.setWindowTitle("NWP Package")
        self.dockWidgetContents = QtWidgets.QWidget(self)

        # Top level layout
        self.vert = QtWidgets.QVBoxLayout(self.dockWidgetContents)

        self.nwp_widget = MainWidget()
        self.vert.addWidget(self.nwp_widget)

        # self.lblTitle = QtWidgets.QLabel("NWP Package")
        # font = self.lblTitle.font()
        # font.setBold(True)
        # font.setPointSize(font.pointSize() + 2)
        # self.lblTitle.setFont(font)
        # self.vert.addWidget(self.lblTitle)

        self.vert.addStretch()

        self.setWidget(self.dockWidgetContents)

    def closeEvent(self, event):
        self.closing.emit()
        for signal in list(self.connections.keys()):
            signal.disconnect(self.connections.pop(signal))
        QtWidgets.QDockWidget.closeEvent(self, event)

    def cleanup_connections(self, *args):
        for signal in list(self.connections.keys()):
            try:
                signal.disconnect(self.connections.pop(signal))
            except Exception:  # nosec B110
                pass
