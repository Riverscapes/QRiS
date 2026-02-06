
from PyQt5 import QtCore, QtGui, QtWidgets

from .utilities import add_standard_form_buttons


class FrmEventPicker(QtWidgets.QDialog):

    def __init__(self, parent, qris_project, event_type_id, layer_name=None, events=None, show_copy_options=False):
        super().__init__(parent=parent)
        self.qris_project = qris_project
        self.event_type_id = event_type_id
        self.show_copy_options = show_copy_options
        self.event_name = "Data Capture Event" if event_type_id == 1 else "Design"
        self.layer_name = layer_name
        self.layers = []
        self.qris_event = None
        self.dce_events = events if events is not None else [event for event in self.qris_project.events.values() if event.event_type.id == event_type_id]
        if self.layer_name is not None:
            # filter events if layer name is within the event layers
            self.dce_events = [event for event in self.dce_events if self.layer_name in [layer.layer.fc_name for layer in event.event_layers]]
        if len(self.dce_events) == 0:
            # warn user with message box and reject the dialog
            filter_message = f" with layer name '{self.layer_name}'" if self.layer_name is not None else ""
            QtWidgets.QMessageBox.warning(self, f"No {self.event_name}s", f"There are no {self.event_name}s{filter_message} in the project.")

        self.setupUi()
        self.setWindowTitle(f"Select {self.event_name}")

        # load list of events filtered by event type
        self.cboDCE.addItems([event.name for event in self.dce_events])
        # initialise the layers list
        self.cboDCE_currentIndexChanged(0)

    def cboDCE_currentIndexChanged(self, index):
        self.layers = []
        self.qris_event = self.dce_events[index]
        for layer in self.qris_event.event_layers:
            self.layers.append(layer.layer)

    def setupUi(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.lblDCE = QtWidgets.QLabel(self.event_name)
        self.horizontalLayout.addWidget(self.lblDCE)

        self.cboDCE = QtWidgets.QComboBox()
        self.cboDCE.currentIndexChanged.connect(self.cboDCE_currentIndexChanged)
        self.horizontalLayout.addWidget(self.cboDCE)

        if self.show_copy_options:
             self.grpOptions = QtWidgets.QGroupBox("Import Options")
             self.vboxOptions = QtWidgets.QVBoxLayout(self.grpOptions)
             
             self.chkLayers = QtWidgets.QCheckBox("Layers")
             self.chkLayers.setChecked(True)
             self.vboxOptions.addWidget(self.chkLayers)
             
             self.chkBasicProps = QtWidgets.QCheckBox("Basic Properties (Date, Platform, etc.)")
             self.chkBasicProps.setChecked(False)
             self.vboxOptions.addWidget(self.chkBasicProps)

             self.chkDescription = QtWidgets.QCheckBox("Description")
             self.chkDescription.setChecked(False)
             self.vboxOptions.addWidget(self.chkDescription)

             self.chkMetadata = QtWidgets.QCheckBox("Metadata")
             self.chkMetadata.setChecked(False)
             self.vboxOptions.addWidget(self.chkMetadata)

             self.verticalLayout.addWidget(self.grpOptions)

        # push the horizontal layout to the top
        self.verticalLayout.addStretch(1)

        # add standard buttons
        help = "dce"
        self.verticalLayout.addLayout(add_standard_form_buttons(self, help))
