# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/mask_attribute.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MaskAttribute(object):
    def setupUi(self, MaskAttribute):
        MaskAttribute.setObjectName("MaskAttribute")
        MaskAttribute.resize(500, 400)
        self.gridLayout_2 = QtWidgets.QGridLayout(MaskAttribute)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(MaskAttribute)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.chkAddToMap = QtWidgets.QCheckBox(MaskAttribute)
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setObjectName("chkAddToMap")
        self.gridLayout.addWidget(self.chkAddToMap, 3, 1, 1, 1)
        self.txtDescription = QtWidgets.QTextEdit(MaskAttribute)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout.addWidget(self.txtDescription, 2, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(MaskAttribute)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.cboType = QtWidgets.QComboBox(MaskAttribute)
        self.cboType.setObjectName("cboType")
        self.gridLayout.addWidget(self.cboType, 1, 1, 1, 1)
        self.txtName = QtWidgets.QLineEdit(MaskAttribute)
        self.txtName.setMaxLength(255)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(MaskAttribute)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 4, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(MaskAttribute)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(MaskAttribute)
        QtCore.QMetaObject.connectSlotsByName(MaskAttribute)
        MaskAttribute.setTabOrder(self.txtName, self.cboType)
        MaskAttribute.setTabOrder(self.cboType, self.txtDescription)

    def retranslateUi(self, MaskAttribute):
        _translate = QtCore.QCoreApplication.translate
        MaskAttribute.setWindowTitle(_translate("MaskAttribute", "Dialog"))
        self.label.setText(_translate("MaskAttribute", "Name"))
        self.chkAddToMap.setText(_translate("MaskAttribute", "Add to Map"))
        self.label_2.setText(_translate("MaskAttribute", "Description"))
        self.label_3.setText(_translate("MaskAttribute", "Type"))
