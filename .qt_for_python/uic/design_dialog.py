# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/nick/Library/Application Support/QGIS/QGIS3/profiles/test/python/plugins/RIPTPlugin/src/ui/design_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_design_dialog(object):
    def setupUi(self, design_dialog):
        design_dialog.setObjectName("design_dialog")
        design_dialog.resize(447, 305)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("/Users/nick/Library/Application Support/QGIS/QGIS3/profiles/test/python/plugins/RIPTPlugin/src/ui/../../icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        design_dialog.setWindowIcon(icon)
        self.formLayout = QtWidgets.QFormLayout(design_dialog)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(design_dialog)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.lineEdit_design_name = QtWidgets.QLineEdit(design_dialog)
        self.lineEdit_design_name.setObjectName("lineEdit_design_name")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit_design_name)
        self.label_2 = QtWidgets.QLabel(design_dialog)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.comboBox_design_source = QtWidgets.QComboBox(design_dialog)
        self.comboBox_design_source.setObjectName("comboBox_design_source")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.comboBox_design_source)
        self.label_4 = QtWidgets.QLabel(design_dialog)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.comboBox_design_type = QtWidgets.QComboBox(design_dialog)
        self.comboBox_design_type.setObjectName("comboBox_design_type")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.comboBox_design_type)
        self.label_5 = QtWidgets.QLabel(design_dialog)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.plainTextEdit_design_description = QtWidgets.QPlainTextEdit(design_dialog)
        self.plainTextEdit_design_description.setObjectName("plainTextEdit_design_description")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.plainTextEdit_design_description)
        self.buttonBox = QtWidgets.QDialogButtonBox(design_dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(design_dialog)
        QtCore.QMetaObject.connectSlotsByName(design_dialog)

    def retranslateUi(self, design_dialog):
        _translate = QtCore.QCoreApplication.translate
        design_dialog.setWindowTitle(_translate("design_dialog", "Low-Tech Design"))
        self.label.setText(_translate("design_dialog", "Design Name"))
        self.label_2.setText(_translate("design_dialog", "Design Source"))
        self.label_4.setText(_translate("design_dialog", "Design Type"))
        self.label_5.setText(_translate("design_dialog", "Design Description"))
