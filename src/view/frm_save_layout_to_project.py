# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore, sip
from qgis.core import QgsProject, QgsPrintLayout, QgsReadWriteContext
from qgis.PyQt.QtXml import QDomDocument

from ..model.layout import save_layout
from .utilities import add_standard_form_buttons

class FrmSaveLayoutToProject(QtWidgets.QDialog):
    def __init__(self, parent, project_file):
        super(FrmSaveLayoutToProject, self).__init__(parent)
        self.setWindowTitle("Save Layout to Project")
        self.project_file = project_file
        
        self.main_layout = QtWidgets.QVBoxLayout(self)
        
        # Instructions
        self.lbl_instructions = QtWidgets.QLabel("Select an open print layout to save to the project:")
        self.main_layout.addWidget(self.lbl_instructions)
        
        # ComboBox for open layouts
        self.cbo_layouts = QtWidgets.QComboBox()
        self.main_layout.addWidget(self.cbo_layouts)
        
        # Name input
        self.lbl_name = QtWidgets.QLabel("Save as (Name):")
        self.main_layout.addWidget(self.lbl_name)
        self.txt_name = QtWidgets.QLineEdit()
        self.main_layout.addWidget(self.txt_name)
        
        # Populate layouts
        self.populate_layouts()
        
        # Buttons
        self.main_layout.addLayout(add_standard_form_buttons(self, "technical-reference/map-templates"))
        
        # Connect signals
        self.cbo_layouts.currentIndexChanged.connect(self.layout_selection_changed)
        self.txt_name.textChanged.connect(self.validate)
        
        # Initial validation
        self.validate()

    def populate_layouts(self):
        project = QgsProject.instance()
        layout_manager = project.layoutManager()
        layouts = layout_manager.printLayouts()
        
        for layout in layouts:
            if isinstance(layout, QgsPrintLayout):
                self.cbo_layouts.addItem(layout.name(), layout)
                
        if self.cbo_layouts.count() > 0:
            self.cbo_layouts.setCurrentIndex(0)
            self.layout_selection_changed(0)
        else:
            self.lbl_instructions.setText("No open print layouts found in QGIS.")
            self.txt_name.setEnabled(False)
            self.cbo_layouts.setEnabled(False)

    def layout_selection_changed(self, index):
        if index >= 0:
            name = self.cbo_layouts.itemText(index)
            self.txt_name.setText(name)

    def validate(self):
        enabled = self.cbo_layouts.count() > 0 and len(self.txt_name.text().strip()) > 0
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)

    def accept(self):
        layout = self.cbo_layouts.currentData()
        name = self.txt_name.text().strip()
        
        if not layout:
             QtWidgets.QMessageBox.warning(self, "Error", "No layout selected.")
             return

        # Ensure layout object has writeXml method (sometimes it comes as QGraphicsScene via PyQt)
        if not hasattr(layout, 'writeXml'):
            try:
                # Try to cast to QgsPrintLayout using sip
                layout = sip.cast(layout, QgsPrintLayout)
            except Exception:
                # If cast fails or sip is not available, we can't save
                pass

        # Check again if writeXml is available after attempt to cast
        if not hasattr(layout, 'writeXml'):
             QtWidgets.QMessageBox.critical(self, "Error Saving Layout", "'writeXml' method not found on layout object. This may be due to a QGIS version incompatibility.")
             return

        # Serialize layout to XML
        doc = QDomDocument()
        context = QgsReadWriteContext()
        element = layout.writeXml(doc, context)
        doc.appendChild(element)
        xml_content = doc.toString()
        
        try:
            save_layout(self.project_file, name, xml_content)
            super().accept()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error Saving Layout", str(e))
