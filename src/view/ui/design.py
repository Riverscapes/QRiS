# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/design.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Design(object):
    def setupUi(self, Design):
        Design.setObjectName("Design")
        Design.resize(600, 400)
        self.gridLayout_2 = QtWidgets.QGridLayout(Design)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(Design)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.txtName = QtWidgets.QLineEdit(Design)
        self.txtName.setMaxLength(255)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(Design)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.cboAssessment = QtWidgets.QComboBox(Design)
        self.cboAssessment.setObjectName("cboAssessment")
        self.gridLayout.addWidget(self.cboAssessment, 1, 1, 1, 1)
        self.label = QtWidgets.QLabel(Design)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.txtDescription = QtWidgets.QTextEdit(Design)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout.addWidget(self.txtDescription, 2, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Design)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Design)
        QtCore.QMetaObject.connectSlotsByName(Design)

    def retranslateUi(self, Design):
        _translate = QtCore.QCoreApplication.translate
        Design.setWindowTitle(_translate("Design", "Dialog"))
        self.label_2.setText(_translate("Design", "Assessment (epoch)"))
        self.label_3.setText(_translate("Design", "Description"))
        self.label.setText(_translate("Design", "Name"))
