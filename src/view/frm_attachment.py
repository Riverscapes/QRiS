import os
import re
import json

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot
from qgis.core import Qgis, QgsApplication

from .widgets.metadata import MetadataWidget
from .utilities import add_standard_form_buttons

from ..gp.copy_file import FileCopyTask
from ..QRiS.path_utilities import parse_posix_path

from ..model.project import Project
from ..model.attachment import Attachment, attachments_path, insert_attachment


class FrmAttachment(QtWidgets.QDialog):

    def __init__(self, parent, iface, project: Project, attachment: Attachment = None, attachment_type: str = Attachment.TYPE_FILE):

        self.iface = iface
        self.project = project
        self.metadata = None
        self.attachment = attachment
        self.attachment_type = attachment_type if attachment is None else attachment.attachment_type
        self.source = FileBrowseWidget() if self.attachment_type == Attachment.TYPE_FILE else WebLinkWidget()
        self.extension = None

        super(FrmAttachment, self).__init__(parent)
        metadata_json = json.dumps(attachment.metadata) if attachment is not None else None
        self.metadata_widget = MetadataWidget(self, metadata_json)
        self.setupUi()

        self.setWindowTitle('Import File Attachment' if self.attachment is None else 'Edit Attachment Properties')

        if self.attachment_type == Attachment.TYPE_WEB_LINK:
            self.lblProjectPath.setEnabled(False)
            self.lblProjectPath.setVisible(False)
            self.txtProjectPath.setEnabled(False)
            self.txtProjectPath.setVisible(False)
            self.lblSource.setText('Web Link')
            self.setWindowTitle('Add Web Link Attachment' if self.attachment is None else 'Edit Web Link Properties')
        else:
            self.txtName.textChanged.connect(self.on_name_changed)

        if self.attachment is None:
            if self.attachment_type == Attachment.TYPE_FILE:
                self.source.lineEdit.textChanged.connect(self.on_path_changed)
        else:
            self.txtName.setText(attachment.name)
            self.txtDescription.setPlainText(attachment.description)
            if self.attachment_type == Attachment.TYPE_FILE:
                self.extension = os.path.splitext(attachment.path)[1]
                self.txtProjectPath.setText(self.attachment.project_path(self.project.project_file))
                self.lblSource.setVisible(False)
                self.source.setEnabled(False)
                self.source.setVisible(False)
            else:
                self.source.lineEdit.setText(attachment.path)


        self.txtName.selectAll()

    def accept(self):

        # make sure there is not already an attachment with the same name
        if self.txtName.text() in [a.name for a in self.project.attachments.values() if a.id != (self.attachment.id if self.attachment else None)]:
            QtWidgets.QMessageBox.warning(self, 'Duplicate Name', f"An attachment with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
            self.txtName.setFocus()
            return
        
        # make sure the new file path will not result in a duplicate name
        if self.attachment_type == Attachment.TYPE_FILE:
            if self.txtProjectPath.text() in [a.path for a in self.project.attachments.values() if a.id != (self.attachment.id if self.attachment else None)]:
                QtWidgets.QMessageBox.warning(self, 'Duplicate Path', f"An attachment with the path '{self.txtProjectPath.text()}' already exists. Please choose a unique path.")
                self.txtProjectPath.setFocus()
                return

        metadata_json = self.metadata_widget.get_json()
        self.metadata = json.loads(metadata_json) if metadata_json is not None else None

        if self.attachment is not None:
            try:
                new_path = self.source.lineEdit.text() if self.attachment_type == Attachment.TYPE_WEB_LINK else os.path.basename(self.txtProjectPath.text())
                if self.attachment_type == Attachment.TYPE_FILE:
                    # Rename the file if the name has changed
                    if self.txtProjectPath.text() != self.attachment.project_path(self.project.project_file):
                        os.rename(self.attachment.project_path(self.project.project_file), self.txtProjectPath.text())

                self.attachment.update(self.project.project_file, self.txtName.text(), path=new_path, description=self.txtDescription.toPlainText(), metadata=self.metadata)
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', f"An attachment with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Attachment', str(ex))
                return

            super().accept()

        else:
            try:
                if self.attachment_type == Attachment.TYPE_FILE:
                    task = FileCopyTask(self.source.lineEdit.text(), self.txtProjectPath.text(), self.on_copy_complete)
                    QgsApplication.taskManager().addTask(task)
                else:
                    # For web links, we don't need to copy files, just create the attachment
                    self.attachment = insert_attachment(self.project.project_file, self.txtName.text(), self.source.lineEdit.text(), self.attachment_type, self.txtDescription.toPlainText(), self.metadata)
                    self.project.attachments[self.attachment.id] = self.attachment
                    super().accept()
            except Exception as ex:
                self.attachment = None
                QtWidgets.QMessageBox.warning(self, 'Error Importing Attachment', str(ex))
                return

    @pyqtSlot(bool)
    def on_copy_complete(self, result: bool, error: str = None):

        if result is True:
            self.iface.messageBar().pushMessage('Feature Class Copy Complete.', f"{self.txtProjectPath.text()} saved successfully.", level=Qgis.Info, duration=5)
        else:
            self.iface.messageBar().pushMessage('Feature Class Copy Error', 'Review the QGIS log.', level=Qgis.Critical, duration=5)
        if error:
            QgsApplication.messageLog().logMessage(f"Error copying file: {error}", "QRiS", Qgis.Critical)
        try:
            self.attachment = insert_attachment(self.project.project_file, self.txtName.text(), os.path.basename(self.txtProjectPath.text()), self.attachment_type, self.txtDescription.toPlainText(), self.metadata)
            self.project.attachments[self.attachment.id] = self.attachment
        except Exception as ex:
            if 'unique' in str(ex).lower():
                QtWidgets.QMessageBox.warning(self, 'Duplicate Name', f"An attachment with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
                self.txtName.setFocus()
            else:
                QtWidgets.QMessageBox.warning(self, 'Error Saving Attachment', str(ex))
            return
        super().accept()

    def on_path_changed(self):
        # get the file name from the source path and set it to the name field
        if self.attachment_type == Attachment.TYPE_FILE:
            file_path = self.source.lineEdit.text()
            if file_path:
                file_name = os.path.basename(file_path)
                # drop the extension
                file_name = os.path.splitext(file_name)[0]
                self.txtName.setText(file_name)
                self.on_name_changed(file_name)
            else:
                self.txtName.setText('')

    def on_name_changed(self, new_name):

        # Replace spaces with underscores and remove non-alphanumeric characters
        clean_name = re.sub('[^A-Za-z0-9_]+', '', self.txtName.text().replace(' ', '_'))
        if len(clean_name) > 0:
            parent_folder = attachments_path(self.project.project_file)
            ext = ''
            if self.attachment_type == Attachment.TYPE_FILE:
                ext = self.extension if self.extension is not None else os.path.splitext(self.source.lineEdit.text())[1]
            self.txtProjectPath.setText(parse_posix_path(os.path.join(parent_folder, self.project.get_safe_file_name(clean_name, ext))))
        else:
            self.txtProjectPath.setText('')

    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)
        self.tabs = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabs)

        self.grid = QtWidgets.QGridLayout()

        self.grid.addWidget(QtWidgets.QLabel('Name'), 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setToolTip('Name of the attachment. This must be unique within the project.')
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblSource = QtWidgets.QLabel('Source Path')
        self.grid.addWidget(self.lblSource, 1, 0, 1, 1)
        self.grid.addWidget(self.source, 1, 1, 1, 1)

        self.lblProjectPath = QtWidgets.QLabel('Project Path')
        self.grid.addWidget(self.lblProjectPath, 3, 0, 1, 1)

        self.txtProjectPath = QtWidgets.QLineEdit()
        self.txtProjectPath.setReadOnly(True)
        self.grid.addWidget(self.txtProjectPath, 3, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel('Description')
        self.lblDescription.setAlignment(QtCore.Qt.AlignTop)
        self.grid.addWidget(self.lblDescription, 5, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription, 5, 1, 1, 1)

        self.tabProperties = QtWidgets.QWidget()
        self.tabs.addTab(self.tabProperties, 'Basic Properties')
        self.tabProperties.setLayout(self.grid)

        # Metadata Tab
        self.tabs.addTab(self.metadata_widget, 'Metadata')

        self.vert.addLayout(add_standard_form_buttons(self, 'attachments'))


class FileBrowseWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(FileBrowseWidget, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        layout.addWidget(self.lineEdit)

        self.browseButton = QtWidgets.QPushButton("...", self)
        self.browseButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.browseButton.clicked.connect(self.browse)
        layout.addWidget(self.browseButton)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

    def browse(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)", options=options)
        if file_path and os.path.isfile(file_path):
            self.lineEdit.setText(file_path)
            return file_path
        return None
    

class WebLinkWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(WebLinkWidget, self).__init__(parent)


        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)  # <--- Add this
        layout.addWidget(self.lineEdit, stretch=1)  # <--- Add stretch

        self.btnPaste = QtWidgets.QPushButton("Paste", self)
        self.btnPaste.clicked.connect(self.paste_link)
        layout.addWidget(self.btnPaste)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

    def paste_link(self):
        clipboard = QtWidgets.QApplication.clipboard()
        web_link = clipboard.text()
        if web_link:
            self.lineEdit.setText(web_link)
