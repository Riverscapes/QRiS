# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/analysis_properties.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AnalysisProperties(object):
    def setupUi(self, AnalysisProperties):
        AnalysisProperties.setObjectName("AnalysisProperties")
        AnalysisProperties.resize(640, 480)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(AnalysisProperties)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.lblName = QtWidgets.QLabel(AnalysisProperties)
        self.lblName.setObjectName("lblName")
        self.gridLayout.addWidget(self.lblName, 0, 0, 1, 1)
        self.cboMask = QtWidgets.QComboBox(AnalysisProperties)
        self.cboMask.setObjectName("cboMask")
        self.gridLayout.addWidget(self.cboMask, 1, 2, 1, 1)
        self.txtName = QtWidgets.QLineEdit(AnalysisProperties)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 2, 1, 1)
        self.cboBasemap = QtWidgets.QComboBox(AnalysisProperties)
        self.cboBasemap.setObjectName("cboBasemap")
        self.gridLayout.addWidget(self.cboBasemap, 2, 2, 1, 1)
        self.txtDescription = QtWidgets.QPlainTextEdit(AnalysisProperties)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout.addWidget(self.txtDescription, 3, 2, 1, 1)
        self.lblBasemap = QtWidgets.QLabel(AnalysisProperties)
        self.lblBasemap.setObjectName("lblBasemap")
        self.gridLayout.addWidget(self.lblBasemap, 2, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(AnalysisProperties)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.lblMask = QtWidgets.QLabel(AnalysisProperties)
        self.lblMask.setObjectName("lblMask")
        self.gridLayout.addWidget(self.lblMask, 1, 0, 1, 1)
        self.chkAddToMap = QtWidgets.QCheckBox(AnalysisProperties)
        self.chkAddToMap.setObjectName("chkAddToMap")
        self.gridLayout.addWidget(self.chkAddToMap, 4, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(AnalysisProperties)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(AnalysisProperties)
        self.buttonBox.accepted.connect(AnalysisProperties.accept)
        self.buttonBox.rejected.connect(AnalysisProperties.reject)
        QtCore.QMetaObject.connectSlotsByName(AnalysisProperties)
        AnalysisProperties.setTabOrder(self.txtName, self.cboMask)
        AnalysisProperties.setTabOrder(self.cboMask, self.cboBasemap)
        AnalysisProperties.setTabOrder(self.cboBasemap, self.txtDescription)

    def retranslateUi(self, AnalysisProperties):
        _translate = QtCore.QCoreApplication.translate
        AnalysisProperties.setWindowTitle(_translate("AnalysisProperties", "Analysis Properties"))
        self.lblName.setText(_translate("AnalysisProperties", "Name"))
        self.lblBasemap.setText(_translate("AnalysisProperties", "Basemap"))
        self.label_3.setText(_translate("AnalysisProperties", "Description"))
        self.lblMask.setText(_translate("AnalysisProperties", "Mask"))
        self.chkAddToMap.setText(_translate("AnalysisProperties", "Add to Map"))
