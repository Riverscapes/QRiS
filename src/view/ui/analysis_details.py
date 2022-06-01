# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/analysis_details.ui'
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
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 1, 1, 1)
        self.lblSegment = QtWidgets.QLabel(Dialog)
        self.lblSegment.setObjectName("lblSegment")
        self.gridLayout.addWidget(self.lblSegment, 1, 0, 1, 1)
        self.txtName_2 = QtWidgets.QLineEdit(Dialog)
        self.txtName_2.setObjectName("txtName_2")
        self.gridLayout.addWidget(self.txtName_2, 0, 1, 1, 1)
        self.txtName = QtWidgets.QLabel(Dialog)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 0, 1, 1)
        self.cboSegment = QtWidgets.QComboBox(Dialog)
        self.cboSegment.setObjectName("cboSegment")
        self.gridLayout.addWidget(self.cboSegment, 1, 1, 1, 1)
        self.tableView = QtWidgets.QTableView(Dialog)
        self.tableView.setObjectName("tableView")
        self.gridLayout.addWidget(self.tableView, 2, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.lblSegment.setText(_translate("Dialog", "Segment"))
        self.txtName.setText(_translate("Dialog", "Name"))
