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
        Assessment.setMinimumSize(QtCore.QSize(300, 400))
        Assessment.setModal(True)
        self.gridLayout_2 = QtWidgets.QGridLayout(Assessment)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.lblDescription = QtWidgets.QLabel(Assessment)
        self.lblDescription.setObjectName("lblDescription")
        self.gridLayout.addWidget(self.lblDescription, 2, 0, 1, 1)
        self.vwMethods = QtWidgets.QListView(Assessment)
        self.vwMethods.setObjectName("vwMethods")
        self.gridLayout.addWidget(self.vwMethods, 1, 1, 1, 1)
        self.txtDescription = QtWidgets.QPlainTextEdit(Assessment)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout.addWidget(self.txtDescription, 2, 1, 1, 1)
        self.lblName = QtWidgets.QLabel(Assessment)
        self.lblName.setObjectName("lblName")
        self.gridLayout.addWidget(self.lblName, 0, 0, 1, 1)
        self.lblMethods = QtWidgets.QLabel(Assessment)
        self.lblMethods.setObjectName("lblMethods")
        self.gridLayout.addWidget(self.lblMethods, 1, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Assessment)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 4, 1, 1, 1)
        self.txtName = QtWidgets.QLineEdit(Assessment)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.chkAddToMap = QtWidgets.QCheckBox(Assessment)
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setObjectName("chkAddToMap")
        self.gridLayout.addWidget(self.chkAddToMap, 3, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Assessment)
        QtCore.QMetaObject.connectSlotsByName(Assessment)
        Assessment.setTabOrder(self.txtName, self.vwMethods)
        Assessment.setTabOrder(self.vwMethods, self.txtDescription)

    def retranslateUi(self, Assessment):
        _translate = QtCore.QCoreApplication.translate
        Assessment.setWindowTitle(_translate("Assessment", "Dialog"))
        self.lblDescription.setText(_translate("Assessment", "Description"))
        self.lblName.setText(_translate("Assessment", "Name"))
        self.lblMethods.setText(_translate("Assessment", "Methods"))
        self.chkAddToMap.setText(_translate("Assessment", "Add Assessment To Map"))
