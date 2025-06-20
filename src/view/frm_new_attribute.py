

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout,QHBoxLayout, QGridLayout, QListWidget, QListWidgetItem, QLabel, QLineEdit, QPushButton


from .utilities import add_standard_form_buttons


class FrmNewAttribute(QDialog):

    def __init__(self, parent, field_name: str = None, attributes: list = None, existing_fields: list = None):
        super(FrmNewAttribute, self).__init__(parent)

        self.name = field_name
        self.attributes = attributes
        self.existing_fields = existing_fields

        if self.existing_fields is not None and self.name in self.existing_fields:
            self.existing_fields.remove(self.name)

        self.setupUi()

        self.setWindowTitle('Add New Attribute')

        if self.name is not None:
            self.txtName.setText(self.name)
        if self.attributes is not None:
            for attribute in self.attributes:
                item = QListWidgetItem(attribute)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.lstAttributes.addItem(item)

    def addItem(self):

        if self.newItemEdit.text() == '':
            return
        
        # check for duplicates
        for i in range(self.lstAttributes.count()):
            if self.lstAttributes.item(i).text() == self.newItemEdit.text():
                return

        item = QListWidgetItem(self.newItemEdit.text())
        item.setCheckState(Qt.Checked)
        self.lstAttributes.addItem(item)
        self.newItemEdit.clear()  # Clear the line edit

    def setupUi(self):

        self.resize(400, 300)
        self.setMinimumSize(QSize(400, 300))

        self.vert = QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QLabel('Field Name')
        self.grid.addWidget(self.lblName, 0, 0)
        self.txtName = QLineEdit()
        self.grid.addWidget(self.txtName, 0, 1)
        
        # listbox of attribute list
        self.lblAttributes = QLabel('Attributes')
        self.grid.addWidget(self.lblAttributes, 1, 0)

        # Line edit and button for adding items
        self.horizAttributeEdit = QHBoxLayout()
        self.newItemEdit = QLineEdit()
        self.horizAttributeEdit.addWidget(self.newItemEdit) 
        self.addItemButton = QPushButton("Add")
        self.addItemButton.clicked.connect(self.addItem)
        self.horizAttributeEdit.addWidget(self.addItemButton)
        self.grid.addLayout(self.horizAttributeEdit, 1, 1)

        self.lstAttributes = QListWidget()
        self.lstAttributes.setSelectionMode(QListWidget.MultiSelection)
        self.grid.addWidget(self.lstAttributes, 2, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'sample-frames'))

    def validate_name(self, name):
        
        if name == '':
            QMessageBox.warning(self, 'Missing Field Name', 'Please enter a name for the new field.')
            return False
        
        if self.existing_fields is not None and name in self.existing_fields:
            QMessageBox.warning(self, 'Duplicate Field Name', 'Please enter a unique name for the new field.')
            return False
        
        return True

    def accept(self):

        name = self.txtName.text()
        if self.validate_name(name) is False:
            return
        
        self.name = name
        # attributes are the checked items in the list
        self.attributes = []
        for i in range(self.lstAttributes.count()):
            if self.lstAttributes.item(i).checkState() == Qt.Checked:
                self.attributes.append(self.lstAttributes.item(i).text())
        super(FrmNewAttribute, self).accept()