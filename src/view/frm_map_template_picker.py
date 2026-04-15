# -*- coding: utf-8 -*-
import os

from qgis.PyQt import QtWidgets, QtCore

from .utilities import add_standard_form_buttons
from ..model.layout import get_project_layouts, get_layout_xml, delete_layout

class FrmMapTemplatePicker(QtWidgets.QDialog):
    def __init__(self, parent=None, project_file=None):
        super(FrmMapTemplatePicker, self).__init__(parent)
        self.setWindowTitle("QRiS Map Template Picker")
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.project_file = project_file

        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Tab 1: System Templates (File-based)
        self.tab_system = QtWidgets.QWidget()
        self.layout_system = QtWidgets.QVBoxLayout(self.tab_system)
        
        self.lbl_system = QtWidgets.QLabel("Select a system template:")
        self.layout_system.addWidget(self.lbl_system)
        
        self.list_system = QtWidgets.QListWidget()
        self.layout_system.addWidget(self.list_system)
        
        self.tabs.addTab(self.tab_system, "System Templates")

        # Tab 2: Project Layouts (DB-based)
        if self.project_file:
            self.tab_project = QtWidgets.QWidget()
            self.layout_project = QtWidgets.QVBoxLayout(self.tab_project)
            
            self.lbl_project = QtWidgets.QLabel("Select a saved project layout:")
            self.layout_project.addWidget(self.lbl_project)
            
            self.list_project = QtWidgets.QListWidget()
            self.layout_project.addWidget(self.list_project)
            
            # Delete button for project layouts
            self.btn_delete = QtWidgets.QPushButton("Delete Selected Layout")
            self.btn_delete.clicked.connect(self.delete_selected_layout)
            self.btn_delete.setEnabled(False)
            self.layout_project.addWidget(self.btn_delete)
            
            self.tabs.addTab(self.tab_project, "Project Layouts")
            self.list_project.itemSelectionChanged.connect(self.selection_changed)

        # Button Box
        self.main_layout.addLayout(add_standard_form_buttons(self, "technical-reference/map-templates"))

        self.selected_template = None
        self.selected_type = None # 'file' or 'xml'
        
        self.load_system_templates()
        if self.project_file:
            self.load_project_layouts()

        # Disable OK button initially
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.list_system.itemSelectionChanged.connect(self.selection_changed)
        self.tabs.currentChanged.connect(self.selection_changed)

    def load_system_templates(self):
        self.list_system.clear()
        directories = self._candidate_template_dirs()
        seen_paths = set()

        for source_label, directory in directories:
            if directory is None or not os.path.isdir(directory):
                continue
            for filename in sorted(os.listdir(directory)):
                if not filename.lower().endswith('.qpt'):
                    continue

                full_path = os.path.join(directory, filename)
                norm_path = os.path.normcase(os.path.normpath(full_path))
                if norm_path in seen_paths:
                    continue
                seen_paths.add(norm_path)

                item = QtWidgets.QListWidgetItem(filename)
                item.setData(QtCore.Qt.UserRole, full_path)
                self.list_system.addItem(item)

    def _candidate_template_dirs(self):
        """Return only the currently open project directory for .qpt discovery."""
        dirs = []
        if self.project_file:
            project_dir = os.path.dirname(self.project_file)
            dirs.append(('Project', project_dir))

        # Preserve order while removing duplicate directories.
        deduped = []
        seen = set()
        for label, directory in dirs:
            if not directory:
                continue
            norm = os.path.normcase(os.path.normpath(directory))
            if norm in seen:
                continue
            seen.add(norm)
            deduped.append((label, directory))

        return deduped

    def load_project_layouts(self):
        self.list_project.clear()
        layouts = get_project_layouts(self.project_file)
        for layout in layouts:
            item = QtWidgets.QListWidgetItem(layout.name)
            item.setData(QtCore.Qt.UserRole, layout.id)
            self.list_project.addItem(item)

    def selection_changed(self):
        current_tab_index = self.tabs.currentIndex()
        if current_tab_index == 0: # System
            enabled = len(self.list_system.selectedItems()) > 0
            self.btn_delete.setEnabled(False) if self.project_file else None
        else: # Project
            enabled = len(self.list_project.selectedItems()) > 0
            if self.project_file:
                self.btn_delete.setEnabled(enabled)
            
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)

    def delete_selected_layout(self):
        if not self.project_file or len(self.list_project.selectedItems()) == 0:
            return
            
        item = self.list_project.selectedItems()[0]
        layout_id = item.data(QtCore.Qt.UserRole)
        
        confirm = QtWidgets.QMessageBox.question(self, "Confirm Delete", 
                                               f"Are you sure you want to delete layout '{item.text()}'?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        
        if confirm == QtWidgets.QMessageBox.Yes:
            delete_layout(self.project_file, layout_id)
            self.load_project_layouts()
            self.selection_changed()

    def accept(self):
        if self.tabs.currentIndex() == 0:
            if len(self.list_system.selectedItems()) > 0:
                self.selected_template = self.list_system.selectedItems()[0].data(QtCore.Qt.UserRole)
                self.selected_type = 'file'
                super().accept()
        else:
            if self.project_file and len(self.list_project.selectedItems()) > 0:
                layout_id = self.list_project.selectedItems()[0].data(QtCore.Qt.UserRole)
                self.selected_template = get_layout_xml(self.project_file, layout_id)
                self.selected_type = 'xml'
                self.selected_name = self.list_project.selectedItems()[0].text()
                super().accept()
        
    def get_template(self):
        return self.selected_type, self.selected_template

