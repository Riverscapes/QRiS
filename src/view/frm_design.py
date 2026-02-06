import sqlite3

from qgis.PyQt import QtCore, QtGui, QtWidgets

from ..model.db_item import DBItem, DBItemModel, dict_factory
from ..model.project import Project
from ..model.event import Event, DESIGN_EVENT_TYPE_ID, DCE_EVENT_TYPE_ID
from ..model.planning_container import PlanningContainer

from .frm_event import FrmEvent
from .widgets.event_library import EventLibraryWidget
from .widgets.planning_event_library import PlanningEventLibraryWidget

class FrmDesign(FrmEvent):

    def __init__(self, parent, qris_project: Project, event_type_id: int, event: Event = None):
        super().__init__(parent, qris_project, event_type_id, event)

        event_type = 'Design' if event_type_id == DESIGN_EVENT_TYPE_ID else 'As-Built Survey'
        self.setWindowTitle(f'Create New {event_type}' if event is None else f'Edit {event_type}')

        self.mandatory_layers = ['complexes']
        self.event_library = PlanningEventLibraryWidget(self, qris_project, [DCE_EVENT_TYPE_ID])

        self.lblPhase.setVisible(True)
        self.txtPhase.setVisible(True)

        self.lblPlatform.setVisible(False)
        self.wdgPlatform.setVisible(False)
        # self.cboPlatform.setVisible(False)
        
        # self.lblRepresentation.setVisible(False)
        # self.cboRepresentation.setVisible(False)
        self.lblDateLabel.setVisible(False)
        self.txtDateLabel.setVisible(False)

        self.lblPercentComplete = QtWidgets.QLabel('Percent Complete', self)
        self.lblPercentComplete.setToolTip('The percentage of the design that has been completed')
        self.tabGrid.addWidget(self.lblPercentComplete, 7, 0)

        self.horiz_slider = QtWidgets.QHBoxLayout()
        self.tabGrid.addLayout(self.horiz_slider, 7, 1, 1, 1)
        self.sliderPercentComplete = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.sliderPercentComplete.setMinimum(0)
        self.sliderPercentComplete.setMaximum(100)
        self.sliderPercentComplete.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.sliderPercentComplete.setTickInterval(5)
        self.sliderPercentComplete.setSingleStep(5)
        self.sliderPercentComplete.update()
        self.sliderPercentComplete.valueChanged.connect(self.adjustSliderValue)
        self.horiz_slider.addWidget(self.sliderPercentComplete)

        init_value = self.sliderPercentComplete.value()
        self.lblPercentCompleteValue = QtWidgets.QLabel(f'{init_value}%', self)
        font_metrics = QtGui.QFontMetrics(self.lblPercentCompleteValue.font())
        text_width = font_metrics.width("100%  ")
        text_height = font_metrics.height()
        self.lblPercentCompleteValue.setMinimumSize(text_width, text_height)
        self.lblPercentCompleteValue.setMaximumSize(text_width, text_height)
        self.horiz_slider.addWidget(self.lblPercentCompleteValue)

        self.lblStatus = QtWidgets.QLabel('Design Status Label', self)
        self.tabGrid.addWidget(self.lblStatus, 8, 0)

        statuses = {key: DBItem('', key, value) for key, value in enumerate(['In Progress', 'Provisional (awaiting review)', 'Final'])}
        self.cboStatus = QtWidgets.QComboBox(self)
        self.cboStatus.setToolTip('The status of the design')
        self.status_model = DBItemModel(statuses)
        self.cboStatus.setModel(self.status_model)
        self.tabGrid.addWidget(self.cboStatus, 8, 1, 1, 1)

        self.lblDesigners = QtWidgets.QLabel(self)
        self.lblDesigners.setText('Designers')
        self.tabGrid.addWidget(self.lblDesigners, 9, 0, 1, 1)

        self.txtDesigners = QtWidgets.QPlainTextEdit(self)
        self.txtDesigners.setToolTip('The name of the designer(s) of the design')
        self.tabGrid.addWidget(self.txtDesigners, 9, 1, 1, 1)

        # Create a checkbox widget for each design source
        self.design_source_widgets, self.design_sources = add_checkbox_widgets(
            self, self.qris_project.project_file, 'lkp_design_sources')

        # Add the checkboxes to the form
        self.lblDesignSources = QtWidgets.QLabel('Design Sources', self)
        self.lblDesignSources.setAlignment(QtCore.Qt.AlignTop)
        self.tabGrid.addWidget(self.lblDesignSources, 10, 0, 1, 1)
        self.groupBoxDesignSources = QtWidgets.QGroupBox(self)
        self.groupBoxDesignSources.setLayout(QtWidgets.QVBoxLayout())
        [self.groupBoxDesignSources.layout().addWidget(widget) for widget in self.design_source_widgets]
        self.tabGrid.addWidget(self.groupBoxDesignSources, 10, 1, 1, 1)

        surface_tab_index = self.tab.indexOf(self.surfaces_widget)
        self.tab.setTabText(surface_tab_index, 'Bases for Design')

        # Add sub-tabs to "Bases for Design"
        self.tabsBases = QtWidgets.QTabWidget()
        self.vert_surfaces.setContentsMargins(9, 9, 9, 9)
        self.vert_surfaces.addWidget(self.tabsBases)

        # Tab 1: Surfaces (Using existing surface library)
        self.tabSurfaces = QtWidgets.QWidget()
        self.vertSurfacesTab = QtWidgets.QVBoxLayout(self.tabSurfaces)
        self.vertSurfacesTab.setContentsMargins(9, 9, 9, 9)
        # Move surface_library from surface_widget (parent) to this new tab
        self.vert_surfaces.removeWidget(self.surface_library)
        self.vertSurfacesTab.addWidget(self.surface_library)
        self.tabsBases.addTab(self.tabSurfaces, 'Surfaces')

        # Tab 2: Data Capture Events
        self.tabDCEs = QtWidgets.QWidget()
        self.vertDCEs = QtWidgets.QVBoxLayout(self.tabDCEs)
        self.vertDCEs.setContentsMargins(9, 9, 9, 9)
        self.tabsBases.addTab(self.tabDCEs, 'Data Capture Events')

        self.grid_based_on_dces = QtWidgets.QGridLayout()
        self.vertDCEs.addLayout(self.grid_based_on_dces)

        self.horiz_planning_container = QtWidgets.QHBoxLayout()
        self.vertDCEs.addLayout(self.horiz_planning_container)

        self.lblPlanningContainer = QtWidgets.QLabel("Select DCE's from:", self)
        self.horiz_planning_container.addWidget(self.lblPlanningContainer)

        self.rdoManual = QtWidgets.QRadioButton("Manually", self)
        self.horiz_planning_container.addWidget(self.rdoManual)

        self.rdoPlanning = QtWidgets.QRadioButton("Planning Container:", self)
        self.horiz_planning_container.addWidget(self.rdoPlanning)

        planning_containers = {key: value for key, value in self.qris_project.planning_containers.items()}
        planning_container_model = DBItemModel(planning_containers)
        planning_container_model._data.sort(key=lambda a: a[0])
        self.cboPlanningContainers = QtWidgets.QComboBox(self)
        self.cboPlanningContainers.setModel(planning_container_model)
        self.cboPlanningContainers.currentIndexChanged.connect(self.on_cboPlanningContainers_currentIndexChanged)
        self.horiz_planning_container.addWidget(self.cboPlanningContainers)
        self.horiz_planning_container.addStretch()

        self.rdoManual.toggled.connect(self.on_rdo_toggled)
        self.rdoPlanning.toggled.connect(self.on_rdo_toggled)

        self.vertDCEs.addSpacing(10)

        self.vertDCEs.addWidget(self.event_library)
        
        # Disable allowing the Planning Container RDO if there are no planning containers
        if len(planning_containers) == 0:
            self.rdoPlanning.setEnabled(False)
            self.cboPlanningContainers.setEnabled(False)
        
        self.rdoManual.setChecked(True)

        if event is not None:
            self.chkAddToMap.setVisible(False)

            if 'system' in self.metadata_widget.metadata:
                # if 'statusId' in self.metadata_widget.metadata['system']:
                #     status_id = self.metadata_widget.metadata['system']['statusId']
                #     status_index = self.status_model.getItemIndexById(status_id)
                #     self.cboStatus.setCurrentIndex(status_index)

                if 'status' in self.metadata_widget.metadata['system']:
                    status = self.metadata_widget.metadata['system']['status']
                    status_index = self.status_model.getItemIndexByName(status)
                    self.cboStatus.setCurrentIndex(status_index)

                if 'designers' in self.metadata_widget.metadata['system']:
                    self.txtDesigners.setPlainText(self.metadata_widget.metadata['system']['designers'])

                if 'designSourceIds' in self.metadata_widget.metadata['system']:
                    design_source_ids = self.metadata_widget.metadata['system']['designSourceIds']
                    if design_source_ids is not None:
                        for source_id in design_source_ids:
                            for widget in self.design_source_widgets:
                                widget_id = widget.property('id')
                                if widget_id == source_id:
                                    widget.setChecked(True)
                if 'percentComplete' in self.metadata_widget.metadata['system']:
                    self.sliderPercentComplete.setValue(int(self.metadata_widget.metadata['system']['percentComplete']))

                if 'planningContainerId' in self.metadata_widget.metadata['system']:
                    planning_container_id = self.metadata_widget.metadata['system']['planningContainerId']
                    planning_container: PlanningContainer = self.qris_project.planning_containers[planning_container_id]
                    planning_container_index = self.cboPlanningContainers.findData(planning_container)
                    self.cboPlanningContainers.setCurrentIndex(planning_container_index)
                    self.rdoPlanning.setChecked(True)
                
                elif 'planning_events' in self.metadata_widget.metadata['system']:
                    meta_planning_events = self.metadata_widget.metadata['system']['planning_events']
                    
                    if isinstance(meta_planning_events, dict):
                        self.event_library.set_event_representations(meta_planning_events)
                    elif isinstance(meta_planning_events, list):
                        ids = [int(i) for i in meta_planning_events]
                        self.event_library.set_selected_event_ids(ids)

                    self.event_library.setEnabled(True)
                else:
                    self.event_library.setEnabled(True)

        else:
            # iterate through available layers to find the first 'complexes' layer
            for p, l in self.layer_widget.available_layers:
                 if 'complexes' in l.id:
                      key = self.layer_widget.get_layer_unique_key(p, l)
                      self.layer_widget.current_layers_state[key] = True
            
            self.layer_widget.full_refresh_ui()

    def on_rdo_toggled(self, checked):
        if not checked:
            return

        if self.rdoManual.isChecked():
            self.cboPlanningContainers.setEnabled(False)
            self.event_library.setEnabled(True)
        else:
            self.cboPlanningContainers.setEnabled(True)
            self.event_library.setEnabled(False)
            self.load_events_from_container()

    def load_events_from_container(self):
        if self.cboPlanningContainers.count() > 0:
            planning_container_id = self.cboPlanningContainers.currentData(QtCore.Qt.UserRole).id
            planning_container: PlanningContainer = self.qris_project.planning_containers[planning_container_id]
            self.event_library.set_event_representations(planning_container.planning_events)

    def on_cboPlanningContainers_currentIndexChanged(self, index):
        if self.rdoPlanning.isChecked():
            self.load_events_from_container()

    def adjustSliderValue(self, value):
        # Calculate the nearest multiple of 5
        adjusted_value = round(value / 5) * 5
        # Set the slider's value to this adjusted value
        # Block signals to prevent infinite loop
        self.sliderPercentComplete.blockSignals(True)
        self.sliderPercentComplete.setValue(adjusted_value)
        self.sliderPercentComplete.blockSignals(False)
        # Update the label
        self.lblPercentCompleteValue.setText(f'{adjusted_value}%')

    def accept(self):

        self.metadata_widget.add_system_metadata('statusId', self.cboStatus.currentData(QtCore.Qt.UserRole).id)
        self.metadata_widget.add_system_metadata('designers', self.txtDesigners.toPlainText())

        design_source_ids = []
        for widget in self.design_source_widgets:
            if widget.isChecked() is True:
                design_source_ids.append(widget.property('id'))

        if len(design_source_ids) > 0:
            self.metadata_widget.add_system_metadata('designSourceIds', design_source_ids)
        else:
            if 'designSourceIds' in self.metadata_widget.metadata['system']:
                self.metadata_widget.delete_item('system', 'designSourceIds')

        self.metadata_widget.add_system_metadata('status', self.cboStatus.currentData(QtCore.Qt.UserRole).name)
        self.metadata_widget.add_system_metadata('percentComplete', self.sliderPercentComplete.value())

        if self.rdoManual.isChecked():
            if 'planningContainerId' in self.metadata_widget.metadata['system']:
                self.metadata_widget.delete_item('system', 'planningContainerId')
            # see if any events have been selected manually. if so, then add them to the metadata.
            planning_events = self.event_library.get_event_representations()
            if len(planning_events) > 0:
                self.metadata_widget.add_system_metadata('planning_events', planning_events)
            elif 'planning_events' in self.metadata_widget.metadata['system']:
                self.metadata_widget.delete_item('system', 'planning_events')
        else:
            planning_container_id = self.cboPlanningContainers.currentData(QtCore.Qt.UserRole).id
            self.metadata_widget.add_system_metadata('planningContainerId', planning_container_id)
            if 'planning_events' in self.metadata_widget.metadata['system']:
                self.metadata_widget.delete_item('system', 'planning_events')

        super().accept()


def add_checkbox_widgets(parent_widget, db_path, table_name):

    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    curs = conn.cursor()
    curs.execute(f'SELECT * FROM {table_name}')
    data = {row['id']: row['name'] for row in curs.fetchall()}
    widget_list = []
    for id, name in data.items():
        widget = QtWidgets.QCheckBox(parent_widget)
        widget.setText(name)
        widget.setProperty('id', id)
        widget_list.append(widget)

    return widget_list, data
