# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/event.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Event(object):
    def setupUi(self, Event):
        Event.setObjectName("Event")
        Event.resize(500, 400)
        Event.setMinimumSize(QtCore.QSize(300, 400))
        Event.setModal(True)
        self.gridLayout_2 = QtWidgets.QGridLayout(Event)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.vwBasis = QtWidgets.QListView(Event)
        self.vwBasis.setObjectName("vwBasis")
        self.gridLayout.addWidget(self.vwBasis, 2, 1, 1, 1)
        self.lblName = QtWidgets.QLabel(Event)
        self.lblName.setObjectName("lblName")
        self.gridLayout.addWidget(self.lblName, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Event)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 8, 1, 1, 1)
        self.vwMethods = QtWidgets.QListView(Event)
        self.vwMethods.setObjectName("vwMethods")
        self.gridLayout.addWidget(self.vwMethods, 1, 1, 1, 1)
        self.label = QtWidgets.QLabel(Event)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(Event)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.lblMethods = QtWidgets.QLabel(Event)
        self.lblMethods.setObjectName("lblMethods")
        self.gridLayout.addWidget(self.lblMethods, 1, 0, 1, 1)
        self.lblDescription = QtWidgets.QLabel(Event)
        self.lblDescription.setObjectName("lblDescription")
        self.gridLayout.addWidget(self.lblDescription, 6, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(Event)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)
        self.chkAddToMap = QtWidgets.QCheckBox(Event)
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setObjectName("chkAddToMap")
        self.gridLayout.addWidget(self.chkAddToMap, 7, 1, 1, 1)
        self.txtDescription = QtWidgets.QPlainTextEdit(Event)
        self.txtDescription.setObjectName("txtDescription")
        self.gridLayout.addWidget(self.txtDescription, 6, 1, 1, 1)
        self.txtName = QtWidgets.QLineEdit(Event)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(Event)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 5, 0, 1, 1)
        self.txtDateDesc = QtWidgets.QLineEdit(Event)
        self.txtDateDesc.setObjectName("txtDateDesc")
        self.gridLayout.addWidget(self.txtDateDesc, 5, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Event)
        QtCore.QMetaObject.connectSlotsByName(Event)
        Event.setTabOrder(self.txtName, self.vwMethods)
        Event.setTabOrder(self.vwMethods, self.txtDescription)

    def retranslateUi(self, Event):
        _translate = QtCore.QCoreApplication.translate
        Event.setWindowTitle(_translate("Event", "Dialog"))
        self.lblName.setText(_translate("Event", "Name"))
        self.label.setText(_translate("Event", "Basemaps"))
        self.label_2.setText(_translate("Event", "Start Date"))
        self.lblMethods.setText(_translate("Event", "Protocols"))
        self.lblDescription.setText(_translate("Event", "Description"))
        self.label_3.setText(_translate("Event", "End Date"))
        self.chkAddToMap.setText(_translate("Event", "Add To Map"))
        self.label_4.setText(_translate("Event", "Date Description"))
