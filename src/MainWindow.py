import os
import sys
from typing import List
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QMessageBox, QDialog, QFileDialog
from PyQt5.QtGui import QAction, QIcon
from PyQt5.QtCore import QSettings, Qt

from view.frm_analysis_explorer import AnalysisExplorerDialog

from __version__ import __version__

COMPANY_NAME = 'NorthArrowResearch'
APP_NAME = 'ChAMPWorkbench'


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        AnalysisExplorerDialog(self).exec_()
