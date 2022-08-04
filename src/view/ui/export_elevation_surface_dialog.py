# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/export_elevation_surface_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_dlgExportPolygon(object):
    def setupUi(self, dlgExportPolygon):
        dlgExportPolygon.setObjectName("dlgExportPolygon")
        dlgExportPolygon.resize(573, 353)
        self.verticalLayout = QtWidgets.QVBoxLayout(dlgExportPolygon)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(dlgExportPolygon)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.txtSurfaceName = QtWidgets.QLineEdit(dlgExportPolygon)
        self.txtSurfaceName.setObjectName("txtSurfaceName")
        self.verticalLayout.addWidget(self.txtSurfaceName)
        self.label_2 = QtWidgets.QLabel(dlgExportPolygon)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.txtSurfacePath = QtWidgets.QLineEdit(dlgExportPolygon)
        self.txtSurfacePath.setReadOnly(True)
        self.txtSurfacePath.setObjectName("txtSurfacePath")
        self.verticalLayout.addWidget(self.txtSurfacePath)
        self.label_3 = QtWidgets.QLabel(dlgExportPolygon)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        self.cboSurfaceType = QtWidgets.QComboBox(dlgExportPolygon)
        self.cboSurfaceType.setObjectName("cboSurfaceType")
        self.verticalLayout.addWidget(self.cboSurfaceType)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QtWidgets.QDialogButtonBox(dlgExportPolygon)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(dlgExportPolygon)
        self.buttonBox.accepted.connect(dlgExportPolygon.accept)
        self.buttonBox.rejected.connect(dlgExportPolygon.reject)
        QtCore.QMetaObject.connectSlotsByName(dlgExportPolygon)

    def retranslateUi(self, dlgExportPolygon):
        _translate = QtCore.QCoreApplication.translate
        dlgExportPolygon.setWindowTitle(_translate("dlgExportPolygon", "Export Elevation Surface"))
        self.label.setText(_translate("dlgExportPolygon", "Polygon Surface Name"))
        self.label_2.setText(_translate("dlgExportPolygon", "Export Path"))
        self.label_3.setText(_translate("dlgExportPolygon", "Polygon Surface Type"))
