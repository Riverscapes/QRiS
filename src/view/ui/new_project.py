# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/new_project.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_NewProject(object):
    def setupUi(self, NewProject):
        NewProject.setObjectName("NewProject")
        NewProject.setWindowModality(QtCore.Qt.ApplicationModal)
        NewProject.resize(563, 481)
        self.verticalLayout = QtWidgets.QVBoxLayout(NewProject)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayoutWidget = QtWidgets.QGridLayout()
        self.gridLayoutWidget.setContentsMargins(-1, -1, 12, -1)
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.txtPath = QtWidgets.QLineEdit(NewProject)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtPath.sizePolicy().hasHeightForWidth())
        self.txtPath.setSizePolicy(sizePolicy)
        self.txtPath.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.txtPath.setReadOnly(True)
        self.txtPath.setObjectName("txtPath")
        self.gridLayoutWidget.addWidget(self.txtPath, 1, 1, 1, 1)
        self.txtProjectName = QtWidgets.QLineEdit(NewProject)
        self.txtProjectName.setMaxLength(255)
        self.txtProjectName.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.txtProjectName.setObjectName("txtProjectName")
        self.gridLayoutWidget.addWidget(self.txtProjectName, 0, 1, 1, 1)
        self.lblName = QtWidgets.QLabel(NewProject)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.lblName.setObjectName("lblName")
        self.gridLayoutWidget.addWidget(self.lblName, 0, 0, 1, 1)
        self.lblPath = QtWidgets.QLabel(NewProject)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblPath.sizePolicy().hasHeightForWidth())
        self.lblPath.setSizePolicy(sizePolicy)
        self.lblPath.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.lblPath.setObjectName("lblPath")
        self.gridLayoutWidget.addWidget(self.lblPath, 1, 0, 1, 1)
        self.txtDescription = QtWidgets.QPlainTextEdit(NewProject)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayoutWidget.addWidget(self.txtDescription, 2, 1, 1, 1)
        self.lblDescription = QtWidgets.QLabel(NewProject)
        self.lblDescription.setObjectName("lblDescription")
        self.gridLayoutWidget.addWidget(self.lblDescription, 2, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(NewProject)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayoutWidget.addWidget(self.buttonBox, 3, 1, 1, 1)
        self.gridLayoutWidget.setColumnStretch(1, 1)
        self.verticalLayout.addLayout(self.gridLayoutWidget)

        self.retranslateUi(NewProject)
        self.buttonBox.accepted.connect(NewProject.accept)
        self.buttonBox.rejected.connect(NewProject.reject)
        QtCore.QMetaObject.connectSlotsByName(NewProject)
        NewProject.setTabOrder(self.txtProjectName, self.txtPath)
        NewProject.setTabOrder(self.txtPath, self.txtDescription)

    def retranslateUi(self, NewProject):
        _translate = QtCore.QCoreApplication.translate
        NewProject.setWindowTitle(_translate("NewProject", "Create New QRiS Project"))
        self.lblName.setText(_translate("NewProject", "Project Name"))
        self.lblPath.setText(_translate("NewProject", "Project Directory"))
        self.lblDescription.setText(_translate("NewProject", "Description"))
