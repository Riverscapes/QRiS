# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/nick/Library/Application Support/QGIS/QGIS3/profiles/test/python/plugins/RIPTPlugin/src/ui/project_layer_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_dlgAddLayer(object):
    def setupUi(self, dlgAddLayer):
        dlgAddLayer.setObjectName("dlgAddLayer")
        dlgAddLayer.resize(552, 410)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("/Users/nick/Library/Application Support/QGIS/QGIS3/profiles/test/python/plugins/RIPTPlugin/src/ui/../../icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        dlgAddLayer.setWindowIcon(icon)
        self.formLayout = QtWidgets.QFormLayout(dlgAddLayer)
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QtWidgets.QLabel(dlgAddLayer)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.lineEdit_import_layer = QtWidgets.QLineEdit(dlgAddLayer)
        self.lineEdit_import_layer.setReadOnly(True)
        self.lineEdit_import_layer.setObjectName("lineEdit_import_layer")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit_import_layer)
        self.label = QtWidgets.QLabel(dlgAddLayer)
        self.label.setObjectName("label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label)
        self.lineEdit_display_name = QtWidgets.QLineEdit(dlgAddLayer)
        self.lineEdit_display_name.setObjectName("lineEdit_display_name")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lineEdit_display_name)
        self.label_3 = QtWidgets.QLabel(dlgAddLayer)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.lineEdit_feature_name = QtWidgets.QLineEdit(dlgAddLayer)
        self.lineEdit_feature_name.setReadOnly(True)
        self.lineEdit_feature_name.setObjectName("lineEdit_feature_name")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.lineEdit_feature_name)
        self.label_5 = QtWidgets.QLabel(dlgAddLayer)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.plainTextEdit_layer_description = QtWidgets.QPlainTextEdit(dlgAddLayer)
        self.plainTextEdit_layer_description.setObjectName("plainTextEdit_layer_description")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.plainTextEdit_layer_description)
        self.buttonBox = QtWidgets.QDialogButtonBox(dlgAddLayer)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.buttonBox)
        self.comboBox_clip_extent = QtWidgets.QComboBox(dlgAddLayer)
        self.comboBox_clip_extent.setObjectName("comboBox_clip_extent")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.comboBox_clip_extent)
        self.label_4 = QtWidgets.QLabel(dlgAddLayer)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_4)

        self.retranslateUi(dlgAddLayer)
        self.buttonBox.accepted.connect(dlgAddLayer.accept)
        self.buttonBox.rejected.connect(dlgAddLayer.reject)
        QtCore.QMetaObject.connectSlotsByName(dlgAddLayer)

    def retranslateUi(self, dlgAddLayer):
        _translate = QtCore.QCoreApplication.translate
        dlgAddLayer.setWindowTitle(_translate("dlgAddLayer", "Import a project layer"))
        self.label_2.setText(_translate("dlgAddLayer", "Import Layer Path:"))
        self.label.setText(_translate("dlgAddLayer", "Display Name"))
        self.label_3.setText(_translate("dlgAddLayer", "Feature Name"))
        self.label_5.setText(_translate("dlgAddLayer", "Layer Description"))
        self.label_4.setText(_translate("dlgAddLayer", "Clip Extent"))
