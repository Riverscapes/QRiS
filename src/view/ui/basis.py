# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/basis.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Basis(object):
    def setupUi(self, Basis):
        Basis.setObjectName("Basis")
        Basis.resize(500, 400)
        self.gridLayout_2 = QtWidgets.QGridLayout(Basis)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(Basis)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.chkAddToMap = QtWidgets.QCheckBox(Basis)
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setObjectName("chkAddToMap")
        self.gridLayout.addWidget(self.chkAddToMap, 5, 1, 1, 1)
        self.lblProjectPath = QtWidgets.QLabel(Basis)
        self.lblProjectPath.setObjectName("lblProjectPath")
        self.gridLayout.addWidget(self.lblProjectPath, 2, 0, 1, 1)
        self.lblClipToMask = QtWidgets.QLabel(Basis)
        self.lblClipToMask.setObjectName("lblClipToMask")
        self.gridLayout.addWidget(self.lblClipToMask, 3, 0, 1, 1)
        self.txtName = QtWidgets.QLineEdit(Basis)
        self.txtName.setMaxLength(255)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Basis)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 6, 1, 1, 1)
        self.txtDescription = QtWidgets.QTextEdit(Basis)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout.addWidget(self.txtDescription, 4, 1, 1, 1)
        self.cboMask = QtWidgets.QComboBox(Basis)
        self.cboMask.setObjectName("cboMask")
        self.gridLayout.addWidget(self.cboMask, 3, 1, 1, 1)
        self.lblSourcePath = QtWidgets.QLabel(Basis)
        self.lblSourcePath.setObjectName("lblSourcePath")
        self.gridLayout.addWidget(self.lblSourcePath, 1, 0, 1, 1)
        self.txtProjectPath = QtWidgets.QLineEdit(Basis)
        self.txtProjectPath.setReadOnly(True)
        self.txtProjectPath.setObjectName("txtProjectPath")
        self.gridLayout.addWidget(self.txtProjectPath, 2, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(Basis)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 4, 0, 1, 1)
        self.txtSourcePath = QtWidgets.QLineEdit(Basis)
        self.txtSourcePath.setReadOnly(True)
        self.txtSourcePath.setObjectName("txtSourcePath")
        self.gridLayout.addWidget(self.txtSourcePath, 1, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Basis)
        QtCore.QMetaObject.connectSlotsByName(Basis)
        Basis.setTabOrder(self.txtName, self.txtProjectPath)
        Basis.setTabOrder(self.txtProjectPath, self.txtDescription)
        Basis.setTabOrder(self.txtDescription, self.chkAddToMap)

    def retranslateUi(self, Basis):
        _translate = QtCore.QCoreApplication.translate
        Basis.setWindowTitle(_translate("Basis", "Dialog"))
        self.label.setText(_translate("Basis", "Name"))
        self.chkAddToMap.setText(_translate("Basis", "Add to Map"))
        self.lblProjectPath.setText(_translate("Basis", "Project path"))
        self.lblClipToMask.setText(_translate("Basis", "Clip to mask"))
        self.lblSourcePath.setText(_translate("Basis", "Source path"))
        self.label_4.setText(_translate("Basis", "Description"))
