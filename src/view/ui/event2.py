# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/event2.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_event2(object):
    def setupUi(self, event2):
        event2.setObjectName("event2")
        event2.resize(640, 480)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(event2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(event2)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.txtName = QtWidgets.QLineEdit(event2)
        self.txtName.setObjectName("txtName")
        self.horizontalLayout.addWidget(self.txtName)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tabWidget = QtWidgets.QTabWidget(event2)
        self.tabWidget.setObjectName("tabWidget")
        self.tabBasic = QtWidgets.QWidget()
        self.tabBasic.setObjectName("tabBasic")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tabBasic)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_3 = QtWidgets.QLabel(self.tabBasic)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.lblProtocols = QtWidgets.QLabel(self.tabBasic)
        self.lblProtocols.setObjectName("lblProtocols")
        self.gridLayout.addWidget(self.lblProtocols, 3, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.tabBasic)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.tabBasic)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 1)
        self.cboPlatform = QtWidgets.QComboBox(self.tabBasic)
        self.cboPlatform.setObjectName("cboPlatform")
        self.gridLayout.addWidget(self.cboPlatform, 2, 1, 1, 1)
        self.vwProtocols = QtWidgets.QListView(self.tabBasic)
        self.vwProtocols.setObjectName("vwProtocols")
        self.gridLayout.addWidget(self.vwProtocols, 3, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem, 1, 0, 1, 1)
        self.tabWidget.addTab(self.tabBasic, "")
        self.tabBasemaps = QtWidgets.QWidget()
        self.tabBasemaps.setObjectName("tabBasemaps")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.tabBasemaps)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.vwBasemaps = QtWidgets.QListView(self.tabBasemaps)
        self.vwBasemaps.setObjectName("vwBasemaps")
        self.gridLayout_4.addWidget(self.vwBasemaps, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabBasemaps, "")
        self.tabDescription = QtWidgets.QWidget()
        self.tabDescription.setObjectName("tabDescription")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tabDescription)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.txtDescription = QtWidgets.QPlainTextEdit(self.tabDescription)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout_3.addWidget(self.txtDescription, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabDescription, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.chkAddToMap = QtWidgets.QCheckBox(event2)
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setObjectName("chkAddToMap")
        self.verticalLayout.addWidget(self.chkAddToMap)
        self.buttonBox = QtWidgets.QDialogButtonBox(event2)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(event2)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(event2)

    def retranslateUi(self, event2):
        _translate = QtCore.QCoreApplication.translate
        event2.setWindowTitle(_translate("event2", "Dialog"))
        self.label.setText(_translate("event2", "Name"))
        self.label_3.setText(_translate("event2", "End Date"))
        self.lblProtocols.setText(_translate("event2", "Protocols"))
        self.label_2.setText(_translate("event2", "Start Date"))
        self.label_4.setText(_translate("event2", "Platform"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabBasic), _translate("event2", "Basic Properties"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabBasemaps), _translate("event2", "Basemaps"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabDescription), _translate("event2", "Description"))
        self.chkAddToMap.setText(_translate("event2", "Add to Map"))
