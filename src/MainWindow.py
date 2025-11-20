import os
import sys
from typing import List
import sqlite3

from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QMessageBox, QDialog, QFileDialog, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSettings, Qt

from .view.frm_analysis_explorer import FrmAnalysisExplorer as AnalysisExplorerDialog
from .model.project import Project, test_project

""" TO MAKE THIS WORK:

1. You need to have this line in your .bashrc or .zshrc or equivalent:
   export QGIS_PATH=/Applications/QGIS.app  <-- Adjust path as needed
2. Set your python interpreter to this path as well.


"""


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('QRiS Standalone')
        self.project: Project | None = None
        self._init_menu()
        self.load_project_interactive()

        if self.project is not None:
            AnalysisExplorerDialog(self, qris_project=self.project).exec_()

    def _init_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        open_action = QAction('Open Project…', self)
        open_action.triggered.connect(self.load_project_interactive)
        file_menu.addAction(open_action)
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def load_project_interactive(self):
        # Prompt user for a GeoPackage project file
        path, _ = QFileDialog.getOpenFileName(self, 'Open QRiS Project', os.path.expanduser('~'), 'GeoPackage (*.gpkg)')
        if not path:
            return
        if not test_project(path):
            QMessageBox.critical(self, 'Invalid Project', 'Selected file is not a valid QRiS project GeoPackage.')
            return
        try:
            self.project = Project(path)
        except Exception as ex:
            QMessageBox.critical(self, 'Load Error', f'Error loading project:\n{ex}')
            self.project = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
