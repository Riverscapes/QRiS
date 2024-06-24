
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets

from ..model.db_item import DBItem, DBItemModel, dict_factory
from ..model.project import Project
from ..model.event import Event, DESIGN_EVENT_TYPE_ID, AS_BUILT_EVENT_TYPE_ID
from .frm_event import FrmEvent


class FrmAsBuilt(FrmEvent):

    def __init__(self, parent, qris_project: Project, event_type_id: int, event: Event = None):
        super().__init__(parent, qris_project, event_type_id, event)

        event_type = 'As-Built'
        self.setWindowTitle(f'Create New {event_type}' if event is None else f'Edit {event_type}')

        self.lblPlatform.setText('As-Built completed at')

        self.lblStatus = QtWidgets.QLabel('Status', self)
        self.tabGrid.addWidget(self.lblStatus, 6, 0)

        statuses = qris_project.lookup_tables['lkp_design_status']
        self.cboStatus = QtWidgets.QComboBox(self)
        self.status_model = DBItemModel(statuses)
        self.cboStatus.setModel(self.status_model)
        self.tabGrid.addWidget(self.cboStatus, 6, 1, 1, 1)

        self.tab.setTabEnabled(0, False)

        self.lblDesigners = QtWidgets.QLabel(self)
        self.lblDesigners.setText('Designers')
        self.tabGrid.addWidget(self.lblDesigners, 7, 0, 1, 1)

        self.txtDesigners = QtWidgets.QPlainTextEdit(self)
        self.tabGrid.addWidget(self.txtDesigners, 7, 1, 1, 1)

        # Create a checkbox widget for each design source
        self.design_source_widgets, self.design_sources = add_checkbox_widgets(
            self, self.qris_project.project_file, 'lkp_design_sources')

        # Add the checkboxes to the form
        self.lblDesignSources = QtWidgets.QLabel('Sources', self)
        self.lblDesignSources.setAlignment(QtCore.Qt.AlignTop)
        self.tabGrid.addWidget(self.lblDesignSources, 8, 0, 1, 1)
        self.groupBoxDesignSources = QtWidgets.QGroupBox(self)
        self.groupBoxDesignSources.setLayout(QtWidgets.QVBoxLayout())
        [self.groupBoxDesignSources.layout().addWidget(widget) for widget in self.design_source_widgets]
        self.tabGrid.addWidget(self.groupBoxDesignSources, 8, 1, 1, 1)

        if event is not None:
            self.chkAddToMap.setVisible(False)

            status_id = event.metadata['statusId']
            status_index = self.status_model.getItemIndexById(status_id)
            self.cboStatus.setCurrentIndex(status_index)

            if 'designers' in event.metadata:
                self.txtDesigners.setPlainText(event.metadata['designers'])

            if 'designSourceIds' in event.metadata:
                design_source_ids = event.metadata['designSourceIds']
                if design_source_ids is not None:
                    for source_id in design_source_ids:
                        for widget in self.design_source_widgets:
                            widget_id = widget.property('id')
                            if widget_id == source_id:
                                widget.setChecked(True)

    def accept(self):

        self.metadata = {
            'statusId': self.cboStatus.currentData(QtCore.Qt.UserRole).id,
            'designers': self.txtDesigners.toPlainText()
        }

        design_source_ids = []
        for widget in self.design_source_widgets:
            if widget.isChecked() is True:
                design_source_ids.append(widget.property('id'))

        if len(design_source_ids) > 0:
            self.metadata['designSourceIds'] = design_source_ids

        self.protocols = [self.qris_project.protocols[5]]
        for protocol in self.protocols:
            for method in protocol.methods:
                for layer in method.layers:
                    layer_si = QtGui.QStandardItem(layer.name)
                    layer_si.setEditable(False)
                    layer_si.setData(layer, QtCore.Qt.UserRole)
                    self.layers_model.appendRow(layer_si)

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
