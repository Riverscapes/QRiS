
import json

from PyQt5 import QtWidgets

from ..model.planning_container import PlanningContainer, insert
from ..model.project import Project

from .widgets.metadata import MetadataWidget
from .widgets.planning_event_library import PlanningEventLibraryWidget

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
        self.event_library = PlanningEventLibraryWidget(self, qris_project, [1, 4, 5])

        self.setupUi()
        self.setWindowTitle(f'Create New Planning Container' if self.planning_container is None else f'Edit Planning Container')

        if self.planning_container is not None:
            self.txtName.setText(self.planning_container.name)
            self.txtDescription.setPlainText(self.planning_container.description)

            events = [event for event in self.qris_project.events.values() if event.id in self.planning_container.planning_events.keys()]
            self.event_library.load_events(events)
            self.event_library.set_event_ids(self.planning_container.planning_events)

        self.txtName.setFocus()

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        events = self.event_library.get_event_values()

        if not self.metadata_widget.validate():
            return

        try:
            if self.planning_container is not None:
                self.planning_container.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), events, self.metadata_widget.get_data())
                super().accept()
            else:
                self.planning_container = insert(
                    self.qris_project.project_file,
                    self.txtName.text(),
                    self.txtDescription.toPlainText(),
                    events,
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

        self.lblName = QtWidgets.QLabel('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setToolTip('The name of the planning container')
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.tab = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tab)

        # Event Library
        if self.event_library is not None:
            self.tab.addTab(self.event_library, 'Associated Events')

        # Description
        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tab.addTab(self.txtDescription, 'Description')

        # Metadata
        self.tab.addTab(self.metadata_widget, 'Metadata')

        help_text = 'events'
        self.vert.addLayout(add_standard_form_buttons(self, help_text))
