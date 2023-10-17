from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class ImportPhotosDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import Photos")
        self.setModal(True)
        self.folder_path = None

        # Create widgets
        self.lbl_folder = QLabel("Folder Path:")
        self.txt_folder = QLineEdit()
        self.btn_browse = QPushButton("Browse")
        self.btn_import = QPushButton("Import")
        self.lbl_preview = QLabel()
        self.lbl_preview.setAlignment(Qt.AlignCenter)

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.lbl_folder)
        layout.addWidget(self.txt_folder)
        layout.addWidget(self.btn_browse)
        layout.addWidget(self.lbl_preview)
        layout.addStretch()
        layout.addWidget(self.btn_import)

        # Connect signals
        self.btn_browse.clicked.connect(self.browse_folder)
        self.btn_import.clicked.connect(self.import_photos)

        # Set layout
        self.setLayout(layout)

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_path = folder_path
            self.txt_folder.setText(folder_path)
            self.show_preview()

    def show_preview(self):
        if self.folder_path:
            # Show first photo in folder as preview
            files = os.listdir(self.folder_path)
            for file in files:
                if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                    file_path = os.path.join(self.folder_path, file)
                    pixmap = QPixmap(file_path)
                    self.lbl_preview.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))
                    break

    def import_photos(self):
        if self.folder_path:
            # Import photos into QGIS
            # TODO: Implement photo import logic
            self.accept()
