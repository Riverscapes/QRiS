# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/add_layer_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_dlgProjectExtent(object):
    def setupUi(self, dlgProjectExtent):
        dlgProjectExtent.setObjectName("dlgProjectExtent")
        dlgProjectExtent.resize(416, 360)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/../../icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        dlgProjectExtent.setWindowIcon(icon)
        self.formLayout = QtWidgets.QFormLayout(dlgProjectExtent)
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QtWidgets.QLabel(dlgProjectExtent)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.lineEdit_import_layer_path = QtWidgets.QLineEdit(dlgProjectExtent)
        self.lineEdit_import_layer_path.setReadOnly(True)
        self.lineEdit_import_layer_path.setObjectName("lineEdit_import_layer_path")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit_import_layer_path)
        self.label = QtWidgets.QLabel(dlgProjectExtent)
        self.label.setObjectName("label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label)
        self.lineEdit_display_name = QtWidgets.QLineEdit(dlgProjectExtent)
        self.lineEdit_display_name.setObjectName("lineEdit_display_name")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lineEdit_display_name)
        self.label_3 = QtWidgets.QLabel(dlgProjectExtent)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.lineEdit_feature_name = QtWidgets.QLineEdit(dlgProjectExtent)
        self.lineEdit_feature_name.setEnabled(True)
        self.lineEdit_feature_name.setAutoFillBackground(False)
        self.lineEdit_feature_name.setReadOnly(True)
        self.lineEdit_feature_name.setObjectName("lineEdit_feature_name")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.lineEdit_feature_name)
        self.label_5 = QtWidgets.QLabel(dlgProjectExtent)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.plainTextEdit_layer_description = QtWidgets.QPlainTextEdit(dlgProjectExtent)
        self.plainTextEdit_layer_description.setObjectName("plainTextEdit_layer_description")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.plainTextEdit_layer_description)
        self.buttonBox = QtWidgets.QDialogButtonBox(dlgProjectExtent)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(dlgProjectExtent)
        self.buttonBox.accepted.connect(dlgProjectExtent.accept)
        self.buttonBox.rejected.connect(dlgProjectExtent.reject)
        QtCore.QMetaObject.connectSlotsByName(dlgProjectExtent)

    def retranslateUi(self, dlgProjectExtent):
        _translate = QtCore.QCoreApplication.translate
        dlgProjectExtent.setWindowTitle(_translate("dlgProjectExtent", "Project Extent"))
        self.label_2.setText(_translate("dlgProjectExtent", "Import Layer Path:"))
        self.label.setText(_translate("dlgProjectExtent", "Display Name"))
        self.label_3.setText(_translate("dlgProjectExtent", "Feature Name"))
        self.label_5.setText(_translate("dlgProjectExtent", "Layer Description"))
