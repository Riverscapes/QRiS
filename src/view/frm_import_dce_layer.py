from PyQt5 import QtWidgets

from ..model.project import Project
from ..model.db_item import DBItem
from ..gp.feature_class_functions import get_field_names

from .utilities import add_standard_form_buttons


class FrmImportDceLayer(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, db_item: DBItem, import_path: str):

        self.qris_project = project
        self.db_item = db_item
        self.import_path = import_path
        self.target_path = f'{project.project_file}|layername={db_item.layer.fc_name}'
        self.qris_event = next(event for event in self.qris_project.events.values() if event.id == db_item.event_id)
        self.field_status = None

        super(FrmImportDceLayer, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle('Import DCE Layer')
        self.txtInputFC.setText(self.import_path)
        self.txtTargetFC.setText(self.db_item.layer.fc_name)
        self.txtEvent.setText(self.qris_event.name)

        self.load_fields()

    def load_fields(self):

        self.tblFields.clearContents()

        input_fields, input_field_types = get_field_names(self.import_path)
        target_fields, target_field_types = get_field_names(self.target_path)

        # create a row for each target field and load the field name
        self.tblFields.setRowCount(len(target_fields))
        for i, field in enumerate(target_fields):
            self.tblFields.setItem(i, 0, QtWidgets.QTableWidgetItem(field))
            self.tblFields.setItem(i, 1, QtWidgets.QTableWidgetItem(target_field_types[i]))
            # create a combo box and load the input fields
            combo = QtWidgets.QComboBox()
            filtered_input_fields = [field for field, field_type in zip(input_fields, input_field_types) if field_type == target_field_types[i]]
            combo.addItems(['-- Do Not Import --'] + filtered_input_fields)
            self.tblFields.setCellWidget(i, 2, combo)
            if self.field_status is not None:
                combo.setCurrentIndex(self.field_status[i])
            else:
                # if the target field name matches the input field name then select it
                if field in filtered_input_fields:
                    combo.setCurrentIndex(combo.findText(field))
                else:
                    combo.setCurrentIndex(0)
            combo.currentIndexChanged.connect(self.validate_fields)

    def validate_fields(self):

        # check that none of the input fields are duplicated, except for the 'Do Not Import' option
        input_fields = []
        valid = True
        for i in range(self.tblFields.rowCount()):
            combo = self.tblFields.cellWidget(i, 2)
            if combo.currentText() != '-- Do Not Import --':
                input_fields.append(combo.currentText())

        for i in range(self.tblFields.rowCount()):
            combo = self.tblFields.cellWidget(i, 2)
            if len(input_fields) == len(set(input_fields)):
                # set the combo box back to original text color
                combo.setStyleSheet('')
                combo.setToolTip('')
            else:
                if combo.currentIndex() > 0 and input_fields.count(combo.currentText()) > 1:
                    combo.setStyleSheet('color: red')
                    # add a tool tip to explain the error
                    combo.setToolTip('Duplicate input field imports not allowed')
                    valid = False
                else:
                    combo.setStyleSheet('')
                    combo.setToolTip('')

        return valid

    def accept(self):

        if not self.validate_fields():
            return

        super(FrmImportDceLayer, self).accept()

    def on_rdoImport_clicked(self):

        # if radio button is checked then enable the table
        if self.rdoImport.isChecked():
            self.tblFields.setEnabled(True)
            self.load_fields()
        else:
            self.field_status = []
            # set all combo boxes to 'Do Not Import'
            for i in range(self.tblFields.rowCount()):
                combo = self.tblFields.cellWidget(i, 2)
                self.field_status.append(combo.currentIndex())
                combo.setCurrentIndex(0)
            self.tblFields.setEnabled(False)

    def setupUi(self):

        self.resize(500, 500)
        self.setMinimumSize(300, 200)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblInputFC = QtWidgets.QLabel('Input Feature Class')
        self.grid.addWidget(self.lblInputFC, 0, 0)
        self.txtInputFC = QtWidgets.QLineEdit()
        self.txtInputFC.setReadOnly(True)
        self.grid.addWidget(self.txtInputFC, 0, 1)

        self.lblEvent = QtWidgets.QLabel('Event')
        self.grid.addWidget(self.lblEvent, 1, 0)
        self.txtEvent = QtWidgets.QLineEdit()
        self.txtEvent.setReadOnly(True)
        self.grid.addWidget(self.txtEvent, 1, 1)

        self.lblTargetFC = QtWidgets.QLabel('Target Feature Class')
        self.grid.addWidget(self.lblTargetFC, 2, 0)
        self.txtTargetFC = QtWidgets.QLineEdit()
        self.txtTargetFC.setReadOnly(True)
        self.grid.addWidget(self.txtTargetFC, 2, 1)

        self.lblFields = QtWidgets.QLabel('Fields')
        self.vert.addWidget(self.lblFields)

        self.horiz = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz)

        self.rdoImport = QtWidgets.QRadioButton('Import Fields')
        self.rdoImport.setChecked(True)
        self.rdoImport.clicked.connect(self.on_rdoImport_clicked)
        self.horiz.addWidget(self.rdoImport)

        self.rdoIgnore = QtWidgets.QRadioButton('Ignore Fields')
        self.rdoIgnore.clicked.connect(self.on_rdoImport_clicked)
        self.horiz.addWidget(self.rdoIgnore)

        self.horiz.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

        self.tblFields = QtWidgets.QTableWidget()
        self.tblFields.setColumnCount(3)
        self.tblFields.setHorizontalHeaderLabels(['Target Fields', 'Data Type', 'Input Fields'])
        self.tblFields.horizontalHeader().setStretchLastSection(True)
        self.tblFields.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tblFields.verticalHeader().setVisible(False)
        self.tblFields.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tblFields.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.vert.addWidget(self.tblFields)

        self.vert.addLayout(add_standard_form_buttons(self, 'import_dce_layer'))
