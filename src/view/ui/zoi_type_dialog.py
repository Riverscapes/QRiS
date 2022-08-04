# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/zoi_type_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_zoi_type_dialog(object):
    def setupUi(self, zoi_type_dialog):
        zoi_type_dialog.setObjectName("zoi_type_dialog")
        zoi_type_dialog.resize(535, 288)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/../../icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        zoi_type_dialog.setWindowIcon(icon)
        self.formLayout = QtWidgets.QFormLayout(zoi_type_dialog)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(zoi_type_dialog)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.lineEdit_zoi_type_name = QtWidgets.QLineEdit(zoi_type_dialog)
        self.lineEdit_zoi_type_name.setObjectName("lineEdit_zoi_type_name")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit_zoi_type_name)
        self.label_5 = QtWidgets.QLabel(zoi_type_dialog)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.plainTextEdit_zoi_type_description = QtWidgets.QPlainTextEdit(zoi_type_dialog)
        self.plainTextEdit_zoi_type_description.setObjectName("plainTextEdit_zoi_type_description")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.plainTextEdit_zoi_type_description)
        self.buttonBox = QtWidgets.QDialogButtonBox(zoi_type_dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(zoi_type_dialog)
        QtCore.QMetaObject.connectSlotsByName(zoi_type_dialog)

    def retranslateUi(self, zoi_type_dialog):
        _translate = QtCore.QCoreApplication.translate
        zoi_type_dialog.setWindowTitle(_translate("zoi_type_dialog", "ZOI Type"))
        self.label.setText(_translate("zoi_type_dialog", "ZOI Type Name"))
        self.lineEdit_zoi_type_name.setPlaceholderText(_translate("zoi_type_dialog", "E.g.,  Bank Erosion"))
        self.label_5.setText(_translate("zoi_type_dialog", "ZOI Type Description"))
        self.plainTextEdit_zoi_type_description.setPlaceholderText(_translate("zoi_type_dialog", "Description of hydrologic,  hydraulic,  geomorphic,  biologica,l  and/or ecological processes."))
