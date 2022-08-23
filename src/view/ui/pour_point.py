# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/pour_point.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PoutPoint(object):
    def setupUi(self, PoutPoint):
        PoutPoint.setObjectName("PoutPoint")
        PoutPoint.resize(640, 480)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(PoutPoint)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.lblName = QtWidgets.QLabel(PoutPoint)
        self.lblName.setObjectName("lblName")
        self.gridLayout.addWidget(self.lblName, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(PoutPoint)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 7, 1, 1, 1)
        self.chkBasinChars = QtWidgets.QCheckBox(PoutPoint)
        self.chkBasinChars.setObjectName("chkBasinChars")
        self.gridLayout.addWidget(self.chkBasinChars, 3, 1, 1, 1)
        self.txtDescription = QtWidgets.QTextEdit(PoutPoint)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout.addWidget(self.txtDescription, 5, 1, 1, 1)
        self.lb = QtWidgets.QLabel(PoutPoint)
        self.lb.setObjectName("lb")
        self.gridLayout.addWidget(self.lb, 1, 0, 1, 1)
        self.txtLongitude = QtWidgets.QLineEdit(PoutPoint)
        self.txtLongitude.setObjectName("txtLongitude")
        self.gridLayout.addWidget(self.txtLongitude, 2, 1, 1, 1)
        self.chkFlowStats = QtWidgets.QCheckBox(PoutPoint)
        self.chkFlowStats.setObjectName("chkFlowStats")
        self.gridLayout.addWidget(self.chkFlowStats, 4, 1, 1, 1)
        self.txtLatitude = QtWidgets.QLineEdit(PoutPoint)
        self.txtLatitude.setObjectName("txtLatitude")
        self.gridLayout.addWidget(self.txtLatitude, 1, 1, 1, 1)
        self.Description = QtWidgets.QLabel(PoutPoint)
        self.Description.setObjectName("Description")
        self.gridLayout.addWidget(self.Description, 5, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(PoutPoint)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.txtName = QtWidgets.QLineEdit(PoutPoint)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout.addLayout(self.verticalLayout, 6, 1, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)

        self.retranslateUi(PoutPoint)
        self.buttonBox.accepted.connect(PoutPoint.accept)
        self.buttonBox.rejected.connect(PoutPoint.reject)
        QtCore.QMetaObject.connectSlotsByName(PoutPoint)
        PoutPoint.setTabOrder(self.txtName, self.txtLatitude)
        PoutPoint.setTabOrder(self.txtLatitude, self.txtLongitude)
        PoutPoint.setTabOrder(self.txtLongitude, self.txtDescription)

    def retranslateUi(self, PoutPoint):
        _translate = QtCore.QCoreApplication.translate
        PoutPoint.setWindowTitle(_translate("PoutPoint", "Dialog"))
        self.lblName.setText(_translate("PoutPoint", "Name"))
        self.chkBasinChars.setText(_translate("PoutPoint", "Retrieve Basin Characteristics"))
        self.lb.setText(_translate("PoutPoint", "Latitude"))
        self.chkFlowStats.setText(_translate("PoutPoint", "Retrieve Flow Statistics"))
        self.Description.setText(_translate("PoutPoint", "TextLabel"))
        self.label_3.setText(_translate("PoutPoint", "Longitude"))
