# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/add_detrended_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_dlgAddDetrended(object):
    def setupUi(self, dlgAddDetrended):
        dlgAddDetrended.setObjectName("dlgAddDetrended")
        dlgAddDetrended.resize(693, 459)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/../../icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        dlgAddDetrended.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(dlgAddDetrended)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(dlgAddDetrended)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.txtRasterName = QtWidgets.QLineEdit(dlgAddDetrended)
        self.txtRasterName.setReadOnly(False)
        self.txtRasterName.setObjectName("txtRasterName")
        self.verticalLayout.addWidget(self.txtRasterName)
        self.label_2 = QtWidgets.QLabel(dlgAddDetrended)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.txtOriginalRasterPath = QtWidgets.QLineEdit(dlgAddDetrended)
        self.txtOriginalRasterPath.setReadOnly(True)
        self.txtOriginalRasterPath.setObjectName("txtOriginalRasterPath")
        self.verticalLayout.addWidget(self.txtOriginalRasterPath)
        self.label_3 = QtWidgets.QLabel(dlgAddDetrended)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        self.txtProjectRasterPath = QtWidgets.QLineEdit(dlgAddDetrended)
        self.txtProjectRasterPath.setReadOnly(True)
        self.txtProjectRasterPath.setObjectName("txtProjectRasterPath")
        self.verticalLayout.addWidget(self.txtProjectRasterPath)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QtWidgets.QDialogButtonBox(dlgAddDetrended)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(dlgAddDetrended)
        self.buttonBox.accepted.connect(dlgAddDetrended.accept)
        self.buttonBox.rejected.connect(dlgAddDetrended.reject)
        QtCore.QMetaObject.connectSlotsByName(dlgAddDetrended)

    def retranslateUi(self, dlgAddDetrended):
        _translate = QtCore.QCoreApplication.translate
        dlgAddDetrended.setWindowTitle(_translate("dlgAddDetrended", "Detrended Raster Properties"))
        self.label.setText(_translate("dlgAddDetrended", "Raster Name:"))
        self.label_2.setText(_translate("dlgAddDetrended", "Original Raster:"))
        self.label_3.setText(_translate("dlgAddDetrended", "Project Raster:"))
