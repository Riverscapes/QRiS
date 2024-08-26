from PyQt5 import QtWidgets, QtCore

from ...model.db_item import DBItem
from ...model.raster import Raster
from ...model.project import Project

class SurfaceLibraryWidget(QtWidgets.QWidget):
# Implement a Surfaces Library grid picker, which loads surfaces in surface library, exposes their date, and type (columns) allows sorting), and has a checkbox 

    def __init__(self, parent: QtWidgets.QWidget, qris_project: Project):
        super().__init__(parent)
        self.qris_project = qris_project
        self.setupUi()

        self.load_surfaces()

    def load_surfaces(self):

        raster_types = self.qris_project.lookup_tables['lkp_raster_types']
        # Load surfaces from the project
        self.table.setRowCount(len(self.qris_project.rasters))
        surface: Raster = None
        for i, surface in enumerate(self.qris_project.rasters.values()):
            # Create a checkbox and add it to the cell widget
            checkBox = QtWidgets.QCheckBox()
            self.table.setCellWidget(i, 0, checkBox)
            
            # Store the entire Raster object in the first column using a custom role
            item = QtWidgets.QTableWidgetItem(surface.name)
            item.setData(QtCore.Qt.UserRole, surface)
            self.table.setItem(i, 1, item)
            
            # Set other surface properties in the table
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(surface.date))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(raster_types[surface.raster_type_id].name))
        
        # resize column 0 to fit the checkboxes
        self.table.setColumnWidth(0, 30)
        self.table.resizeColumnsToContents()

        if len(self.qris_project.rasters) == 0:
            self.table.setRowCount(1)
            no_surfaces_item = QtWidgets.QTableWidgetItem('No surfaces have been loaded in this QRiS project')
            font = no_surfaces_item.font()
            font.setItalic(True)
            no_surfaces_item.setFont(font)
            self.table.setItem(0, 0, no_surfaces_item)
            self.table.setSpan(0, 0, 1, 4)
            self.table.setShowGrid(False)
            self.table.resizeColumnsToContents()
            self.table.horizontalHeader().hide()
            self.btnSelectAll.hide()
            self.btnDeselectAll.hide()

    def set_selected_surface_ids(self, selected_surfaces: list):
        # set a list of selected surfaces by their ids

        for i in range(self.table.rowCount()):
            # Skip the row with the "No surfaces available" message
            if self.table.item(i, 0) and self.table.item(i, 0).text() == "No surfaces have been loaded in this QRiS project":
                continue
            surface: Raster = self.table.item(i, 1).data(QtCore.Qt.UserRole)
            if surface.id in selected_surfaces:
                self.table.cellWidget(i, 0).setChecked(True)


    def get_selected_surfaces(self) -> list:
        # Return the selected surfaces by object

        selected_surfaces = []
        for i in range(self.table.rowCount()):
            # Skip the row with the "No surfaces available" message
            if self.table.item(i, 0) and self.table.item(i, 0).text() == "No surfaces have been loaded in this QRiS project":
                continue
            if self.table.cellWidget(i, 0).isChecked():
                surface: Raster = self.table.item(i, 1).data(QtCore.Qt.UserRole)
                selected_surfaces.append(surface)
        return selected_surfaces
    
    def get_selected_surface_ids(self) -> list:
        # Return the selected surfaces by id

        selected_surfaces = []
        for i in range(self.table.rowCount()):
            # Skip the row with the "No surfaces available" message
            if self.table.item(i, 0) and self.table.item(i, 0).text() == "No surfaces have been loaded in this QRiS project":
                continue
            if self.table.cellWidget(i, 0).isChecked():
                surface: Raster = self.table.item(i, 1).data(QtCore.Qt.UserRole)
                selected_surfaces.append(surface.id)
        return selected_surfaces

    def select_all(self):
        for i in range(self.table.rowCount()):
            self.table.cellWidget(i, 0).setChecked(True)

    def deselect_all(self):
        for i in range(self.table.rowCount()):
            self.table.cellWidget(i, 0).setChecked(False)

    def setupUi(self):

        self.vert_layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['', 'Name', 'Date', 'Type'])
        # self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.vert_layout.addWidget(self.table)

        self.horiz_layout = QtWidgets.QHBoxLayout()
        self.vert_layout.addLayout(self.horiz_layout)

        self.horiz_layout.addStretch()

        self.btnSelectAll = QtWidgets.QPushButton('Select All')
        self.btnSelectAll.clicked.connect(self.select_all)
        self.horiz_layout.addWidget(self.btnSelectAll)

        self.btnDeselectAll = QtWidgets.QPushButton('Select None')
        self.btnDeselectAll.clicked.connect(self.deselect_all)
        self.horiz_layout.addWidget(self.btnDeselectAll)


        self.setLayout(self.vert_layout)

