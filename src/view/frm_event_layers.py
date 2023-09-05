
from PyQt5 import QtCore, QtGui, QtWidgets

from .utilities import add_standard_form_buttons


class FrmAddFromDCE(QtWidgets.QDialog):

    def __init__(self, parent, qris_project, event_type_id, copy_features=False):
        super().__init__(parent=parent)
        self.qris_project = qris_project
        self.event_type_id = event_type_id
        self.copy_features = copy_features
        self.layers = []
        self.dce_events = [event for event in self.qris_project.events.values() if event.event_type.id == event_type_id]
        self.event_name = "Data Capture Event" if event_type_id == 1 else "Design"
        self.setupUi()

        # load list of events filtered by event type
        self.cboDCE.addItems([event.name for event in self.dce_events])

    def cboDCE_currentIndexChanged(self, index):
        self.layers = []
        for layer in self.dce_events[index].event_layers:
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

        # add standard buttons
        help = "events"
        self.verticalLayout.addLayout(add_standard_form_buttons(self, help))
