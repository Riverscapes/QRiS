
import json

from PyQt5 import QtCore, QtGui, QtWidgets

from ..model.event import Event, AS_BUILT_EVENT_TYPE_ID, AS_BUILT_MACHINE_CODE, DESIGN_EVENT_TYPE_ID
from ..model.planning_container import PlanningContainer, insert
from ..model.db_item import DBItem, DBItemModel
from ..model.datespec import DateSpec
from ..model.project import Project


from .frm_date_picker import FrmDatePicker
from .widgets.metadata import MetadataWidget
from .widgets.surface_library import SurfaceLibraryWidget
from .widgets.event_library import EventLibraryWidget

from datetime import date, datetime
from .utilities import validate_name, add_standard_form_buttons


class FrmPlanningContainer(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, planning_container: PlanningContainer = None):
        super().__init__(parent)

        self.qris_project = qris_project
        self.planning_container = planning_container

        init_metadata = None
        if self.planning_container is not None and self.planning_container.metadata is not None:
            # move any keys that are not 'metadata', 'system' or 'attributes' to 'system'
            init_metadata = self.planning_container.metadata
            if 'system' not in init_metadata:
                init_metadata['system'] = dict()
            for key in list(init_metadata.keys()):
                if key not in ['metadata', 'system', 'attributes']:
                    init_metadata['system'][key] = init_metadata[key]
                    del init_metadata[key]
        self.metadata_widget = MetadataWidget(self, json.dumps(init_metadata))
        self.layer_widget = None
        self.event_library = None
        self.event_library = EventLibraryWidget(self, qris_project, [1, 4, 5])

        self.setupUi()
        self.setWindowTitle(f'Create New Planning Container' if self.planning_container is None else f'Edit Planning Container')

        self.platform_model = DBItemModel(qris_project.lookup_tables['lkp_platform'])
        self.representation_model = DBItemModel(qris_project.lookup_tables['lkp_representation'])
        self.representation_model._data.sort(key=lambda a: a[0])
        self.cboPlatform.setModel(self.platform_model)
        self.cboRepresentation.setModel(self.representation_model)

        self.optSingleDate.toggled.connect(self.on_opt_date_change)

        valley_bottoms: dict = qris_project.valley_bottoms.copy()
        valley_bottoms[0] = DBItem('', 0, 'None')
        self.valley_bottom_model = DBItemModel(valley_bottoms)
        self.valley_bottom_model.sort_data_by_key()
        self.cboValleyBottom.setModel(self.valley_bottom_model)
        self.cboValleyBottom.setCurrentIndex(0)

        if self.planning_container is not None:
            self.txtName.setText(self.planning_container.name)
            self.txtDescription.setPlainText(self.planning_container.description)
            # self.cboPlatform.setCurrentIndex(self.planning_container.platform.id - 1)
            # self.cboRepresentation.setCurrentIndex(self.planning_container.representation.id - 1)

            # self.uc_start.set_date_spec(self.planning_container.start)
            # self.uc_end.set_date_spec(self.planning_container.end)
            # if any(date is not None for date in [self.planning_container.end.day, self.planning_container.end.year, self.planning_container.end.month]):
            #     self.optDateRange.setChecked(True)

            if self.metadata_widget.metadata is not None and 'system' in self.metadata_widget.metadata:
                if 'valley_bottom_id' in self.metadata_widget.metadata['system']:
                    self.cboValleyBottom.setCurrentIndex(self.valley_bottom_model.getItemIndexById(self.metadata_widget.metadata['system']['valley_bottom_id']))
                if 'phase' in self.metadata_widget.metadata['system']:
                    self.txtPhase.setText(self.metadata_widget.metadata['system']['phase'])


            # self.surface_library.set_selected_surface_ids([r.id for r in self.planning_container.rasters])

        self.txtName.setFocus()

    def on_opt_date_change(self):
        if self.optSingleDate.isChecked():
            self.lblEndDate.setVisible(False)
            self.uc_end.setVisible(False)
            self.lblStartDate.setText('Date')
        else:
            self.lblEndDate.setVisible(True)
            self.uc_end.setVisible(True)
            self.lblStartDate.setText('Start Date')

    # def check_surface_types(self):
    #     """check that only one surface type of id == 4 is checked"""

    #     checked_dems = 0
    #     for raster in self.surface_library.get_selected_surfaces():
    #         if raster.raster_type_id == 4:
    #             checked_dems += 1
    #     return False if checked_dems > 1 else True

    def accept(self):


        # if not self.check_surface_types():
        #     QtWidgets.QMessageBox.warning(self, 'Invalid Surface Types', 'Only one DEM can be selected')
        #     return

        start_date_valid, start_date_error_msg = self.uc_start.validate()
        if not start_date_valid:
            QtWidgets.QMessageBox.warning(self, 'Invalid Start Date', start_date_error_msg)
            self.uc_start.setFocus()
            return

        end_date_valid, end_date_error_msg = self.uc_end.validate()
        if not end_date_valid:
            QtWidgets.QMessageBox.warning(self, 'Invalid End Date', end_date_error_msg)
            self.uc_end.setFocus()
            return

        start_date = self.uc_start.get_date_spec()
        end_date = self.uc_end.get_date_spec()

        date_order_valid = check_if_date_order_valid(start_date, end_date)
        if not date_order_valid:
            QtWidgets.QMessageBox.warning(self, 'Invalid Date Order', "Start date must be before the end date.")
            self.uc_end.setFocus()
            return

        if not validate_name(self, self.txtName):
            return

        # surface_rasters = self.surface_library.get_selected_surfaces()
        
        if self.cboValleyBottom.currentText() != 'None':
            self.metadata_widget.add_system_metadata('valley_bottom_id', self.cboValleyBottom.currentData(QtCore.Qt.UserRole).id)
        else:
            self.metadata_widget.delete_item('system', 'valley_bottom_id')

        if self.txtPhase.text() != '':
            self.metadata_widget.add_system_metadata('phase', self.txtPhase.text())
        else:
            self.metadata_widget.delete_item('system', 'phase')

        if not self.metadata_widget.validate():
            return

        try:
            if self.planning_container is not None:
                self.planning_container.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), [], self.metadata_widget.get_data())
                super().accept()
            else:
                self.planning_container = insert(
                    self.qris_project.project_file,
                    self.txtName.text(),
                    self.txtDescription.toPlainText(),
                    [],
                    self.metadata_widget.get_data()
                )

                self.qris_project.planning_containers[self.planning_container.id] = self.planning_container
                super().accept()

        except Exception as ex:
            if 'unique' in str(ex).lower():
                QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A data capture event with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                self.txtName.setFocus()
            else:
                QtWidgets.QMessageBox.warning(self, 'Error Saving Data Capture Event', str(ex))

    def setupUi(self):

        self.resize(575, 550)
        self.setMinimumSize(500, 400)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.tab = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tab)

        # Layers Tab
        if self.layer_widget is not None:
            self.tab.addTab(self.layer_widget, 'Layers')        

        # Basic Properties Tab
        self.tabGridWidget = QtWidgets.QWidget()
        self.tabGrid = QtWidgets.QGridLayout(self.tabGridWidget)
        self.tab.addTab(self.tabGridWidget, 'Basic Properties')

        self.lblValleyBottom = QtWidgets.QLabel('Associated Valley Bottom')
        self.tabGrid.addWidget(self.lblValleyBottom, 0, 0, 1, 1)

        self.cboValleyBottom = QtWidgets.QComboBox()
        self.tabGrid.addWidget(self.cboValleyBottom, 0, 1, 1, 1)

        # row 2: as-built associated design

        self.lblPhase = QtWidgets.QLabel('Phase', self)
        self.tabGrid.addWidget(self.lblPhase, 2, 0, 1, 1)
        self.lblPhase.setVisible(False)

        self.txtPhase = QtWidgets.QLineEdit(self)
        self.txtPhase.setPlaceholderText('Phase 1, Phase 2, Pilot, Demo, Maintenance of Phase 1 etc.')
        self.tabGrid.addWidget(self.txtPhase, 2, 1, 1, 1)
        self.txtPhase.setVisible(False)

        self.optSingleDate = QtWidgets.QRadioButton('Single Point in Time')
        self.optSingleDate.setChecked(True)
        self.tabGrid.addWidget(self.optSingleDate, 3, 0, 1, 1)

        self.optDateRange = QtWidgets.QRadioButton('Date Range')
        self.tabGrid.addWidget(self.optDateRange, 4, 0, 1, 1)

        self.lblStartDate = QtWidgets.QLabel()
        self.lblStartDate.setText('Date')
        self.tabGrid.addWidget(self.lblStartDate, 5, 0, 1, 1)

        self.uc_start = FrmDatePicker(self)
        self.tabGrid.addWidget(self.uc_start, 5, 1, 1, 1)

        self.lblEndDate = QtWidgets.QLabel()
        self.lblEndDate.setText('End Date')
        self.lblEndDate.setVisible(False)
        self.tabGrid.addWidget(self.lblEndDate, 6, 0, 1, 1)

        self.uc_end = FrmDatePicker(self)
        self.uc_end.setVisible(False)
        self.tabGrid.addWidget(self.uc_end, 6, 1, 1, 1)

        self.lblPlatform = QtWidgets.QLabel()
        self.lblPlatform.setText('Event completed at')
        self.tabGrid.addWidget(self.lblPlatform, 7, 0, 1, 1)

        self.cboPlatform = QtWidgets.QComboBox()
        self.tabGrid.addWidget(self.cboPlatform, 7, 1, 1, 1)

        self.lblRepresentation = QtWidgets.QLabel("Representation")
        self.tabGrid.addWidget(self.lblRepresentation, 8, 0, 1, 1)

        self.cboRepresentation = QtWidgets.QComboBox()
        self.tabGrid.addWidget(self.cboRepresentation, 8, 1, 1, 1)

        verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.tabGrid.addItem(verticalSpacer)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(False)
        self.chkAddToMap.setText('Add New Layers to Map')
        self.vert.addWidget(self.chkAddToMap)

        # Surface Rasters
        if self.event_library is not None:
            self.tab.addTab(self.event_library, 'Associated Events')
        
        # self.vert_surfaces = QtWidgets.QVBoxLayout(self)
        # self.surfaces_widget = QtWidgets.QWidget(self)
        # self.surfaces_widget.setLayout(self.vert_surfaces)
        # self.vert_surfaces.addWidget(self.surface_library)
        # self.tab.addTab(self.surfaces_widget, 'Surfaces')
        # self.tab.addTab(self.surface_library, 'Surfaces')

        # Description
        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tab.addTab(self.txtDescription, 'Description')

        # Metadata
        self.tab.addTab(self.metadata_widget, 'Metadata')

        help_text = 'events'
        self.vert.addLayout(add_standard_form_buttons(self, help_text))


def check_if_date_order_valid(start_date: DateSpec, end_date: DateSpec):
    if start_date.year is None or end_date.month is None:
        return True
    elif start_date.month is None or end_date.month is None:
        if start_date.year <= end_date.year:
            return True
        else:
            return False
    elif start_date.day is None or end_date.day is None:
        start_dt = datetime(start_date.year, start_date.month, 1)
        end_dt = datetime(end_date.year, end_date.month, 1)
    else:
        start_dt = datetime(start_date.year, start_date.month, start_date.day)
        end_dt = datetime(end_date.year, end_date.month, end_date.day)

    if start_dt > end_dt:
        return False
    else:
        return True
