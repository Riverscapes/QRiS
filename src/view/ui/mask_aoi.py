# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/mask_aoi.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MaskAOI(object):
    def setupUi(self, MaskAOI):
        MaskAOI.setObjectName("MaskAOI")
        MaskAOI.resize(500, 400)
        self.gridLayout_2 = QtWidgets.QGridLayout(MaskAOI)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(MaskAOI)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.chkAddToMap = QtWidgets.QCheckBox(MaskAOI)
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setObjectName("chkAddToMap")
        self.gridLayout.addWidget(self.chkAddToMap, 3, 1, 1, 1)
        self.txtDescription = QtWidgets.QTextEdit(MaskAOI)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout.addWidget(self.txtDescription, 2, 1, 1, 1)
        self.label = QtWidgets.QLabel(MaskAOI)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.txtName = QtWidgets.QLineEdit(MaskAOI)
        self.txtName.setMaxLength(255)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(MaskAOI)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 4, 1, 1, 1)
        self.cboAttribute = QtWidgets.QComboBox(MaskAOI)
        self.cboAttribute.setObjectName("cboAttribute")
        self.gridLayout.addWidget(self.cboAttribute, 1, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(MaskAOI)
        QtCore.QMetaObject.connectSlotsByName(MaskAOI)
        MaskAOI.setTabOrder(self.txtName, self.txtDescription)

    def retranslateUi(self, MaskAOI):
        _translate = QtCore.QCoreApplication.translate
        MaskAOI.setWindowTitle(_translate("MaskAOI", "Dialog"))
        self.label_2.setText(_translate("MaskAOI", "Description"))
        self.chkAddToMap.setText(_translate("MaskAOI", "Add to Map"))
        self.label.setText(_translate("MaskAOI", "Name"))
