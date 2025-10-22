from PyQt5 import QtWidgets, QtCore


class FrmLayerTypeDialog(QtWidgets.QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Layer to QRiS Project...")
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel("Add this layer as:")
        self.combo = QtWidgets.QComboBox()
        self.combo.addItems(items)
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(label)
        layout.addWidget(self.combo)
        layout.addWidget(btn_box)

    def selected_type(self):
        return self.combo.currentText()
