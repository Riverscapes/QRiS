# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/assessment.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Assessment(object):
    def setupUi(self, Assessment):
        Assessment.setObjectName("Assessment")
        Assessment.resize(640, 480)
        self.gridLayoutWidget = QtWidgets.QWidget(Assessment)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(29, 19, 581, 421))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(self.gridLayoutWidget)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 1, 1, 1)
        self.lblName = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lblName.setObjectName("lblName")
        self.gridLayout.addWidget(self.lblName, 0, 0, 1, 1)
        self.txtName = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.lblMethods = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lblMethods.setObjectName("lblMethods")
        self.gridLayout.addWidget(self.lblMethods, 1, 0, 1, 1)
        self.lblDescription = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lblDescription.setObjectName("lblDescription")
        self.gridLayout.addWidget(self.lblDescription, 2, 0, 1, 1)
        self.plainTextEdit = QtWidgets.QPlainTextEdit(self.gridLayoutWidget)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.gridLayout.addWidget(self.plainTextEdit, 2, 1, 1, 1)
        self.vwMethods = QtWidgets.QListView(self.gridLayoutWidget)
        self.vwMethods.setObjectName("vwMethods")
        self.gridLayout.addWidget(self.vwMethods, 1, 1, 1, 1)

        self.retranslateUi(Assessment)
        QtCore.QMetaObject.connectSlotsByName(Assessment)

    def retranslateUi(self, Assessment):
        _translate = QtCore.QCoreApplication.translate
        Assessment.setWindowTitle(_translate("Assessment", "Dialog"))
        self.lblName.setText(_translate("Assessment", "TextLabel"))
        self.lblMethods.setText(_translate("Assessment", "Methods"))
        self.lblDescription.setText(_translate("Assessment", "Description"))
