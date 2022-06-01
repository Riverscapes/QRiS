# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/new_analysis.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(640, 480)
        self.gridLayout_2 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.txtName = QtWidgets.QLineEdit(Dialog)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.txtDescription = QtWidgets.QTextEdit(Dialog)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout.addWidget(self.txtDescription, 2, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 1, 1, 1)
        self.cboMask = QtWidgets.QComboBox(Dialog)
        self.cboMask.setObjectName("cboMask")
        self.gridLayout.addWidget(self.cboMask, 1, 1, 1, 1)
        self.lblMask = QtWidgets.QLabel(Dialog)
        self.lblMask.setObjectName("lblMask")
        self.gridLayout.addWidget(self.lblMask, 1, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_2.setText(_translate("Dialog", "TextLabel"))
        self.label.setText(_translate("Dialog", "TextLabel"))
        self.lblMask.setText(_translate("Dialog", "TextLabel"))
