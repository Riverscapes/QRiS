from PyQt5 import QtWidgets


from .utilities import add_standard_form_buttons


class FrmExportMetrics(QtWidgets.QDialog):

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Export Metrics Table")
        self.setupUi()

    def browse_path(self):

        output_format = self.combo_format.currentText()
        output_ext = "xlsx" if output_format == "Excel" else output_format.lower()

        path = QtWidgets.QFileDialog.getSaveFileName(self, "Export Metrics Table", "", f"{output_format} Files (*.{output_ext})")[0]
        self.txtOutpath.setText(path)

    def format_change(self):

        # if the edit_location is not empty, then change the extension to match the new format
        if self.txtOutpath.text() != "":
            path = self.txtOutpath.text()
            output_format = self.combo_format.currentText()
            if output_format == "Excel":
                output_format = "xlsx"
            path = path[:path.rfind(".") + 1] + output_format.lower()
            self.txtOutpath.setText(path)

    def accept(self) -> None:

        if not self.txtOutpath.text():
            QtWidgets.QMessageBox.warning(self, "Export Metrics Table", "Please specify an output file.")
            return

        return super().accept()

    def setupUi(self):

        self.setMinimumSize(500, 300)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        # Groupbox named "Data Capture Events" with radio buttons for "just the currently active DCE" or "All Data Capture Events"
        self.grpDCE = QtWidgets.QGroupBox('Data Capture Events')
        self.rdoActiveDCE = QtWidgets.QRadioButton('Just the currently active Data Capture Event')
        self.rdoAllDCE = QtWidgets.QRadioButton('All Data Capture Events')
        self.rdoActiveDCE.setChecked(True)
        self.grpDCE.setLayout(QtWidgets.QVBoxLayout())
        self.grpDCE.layout().addWidget(self.rdoActiveDCE)
        self.grpDCE.layout().addWidget(self.rdoAllDCE)
        self.vert.addWidget(self.grpDCE)

        # groupbox named Sampling Frames with radio buttons for "just the currently active SF" or "All Sampling Frames"
        self.grpSF = QtWidgets.QGroupBox('Sampling Frames')
        self.rdoActiveSF = QtWidgets.QRadioButton('Just the currently active Sampling Frame')
        self.rdoAllSF = QtWidgets.QRadioButton('All Sampling Frames')
        self.rdoActiveSF.setChecked(True)
        self.grpSF.setLayout(QtWidgets.QVBoxLayout())
        self.grpSF.layout().addWidget(self.rdoActiveSF)
        self.grpSF.layout().addWidget(self.rdoAllSF)
        self.vert.addWidget(self.grpSF)

        self.export_grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.export_grid)

        # label for export format
        self.lbl_format = QtWidgets.QLabel("Export Format")
        self.export_grid.addWidget(self.lbl_format, 0, 0, 1, 1)

        self.horiz_format = QtWidgets.QHBoxLayout()
        self.export_grid.addLayout(self.horiz_format, 0, 1, 1, 1)

        # drop down for export format
        self.combo_format = QtWidgets.QComboBox()
        self.combo_format.addItems(["CSV", "JSON"])  # , "Excel"
        self.combo_format.currentTextChanged.connect(self.format_change)
        self.horiz_format.addWidget(self.combo_format)

        # add spacer
        self.horiz_format.addStretch()

        # label for export location
        self.lbl_location = QtWidgets.QLabel("Export Path")
        self.export_grid.addWidget(self.lbl_location, 1, 0, 1, 1)

        self.horizOutput = QtWidgets.QHBoxLayout()
        self.export_grid.addLayout(self.horizOutput, 1, 1, 1, 1)

        # line edit for export location
        self.txtOutpath = QtWidgets.QLineEdit()
        self.txtOutpath.setReadOnly(True)
        self.horizOutput.addWidget(self.txtOutpath)

        # button for export location
        self.btn_location = QtWidgets.QPushButton("...")
        self.btn_location.clicked.connect(self.browse_path)
        self.horizOutput.addWidget(self.btn_location)

        # add standard form buttons
        self.vert.addLayout(add_standard_form_buttons(self, "export_metrics"))
