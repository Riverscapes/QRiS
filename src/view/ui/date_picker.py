# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/date_picker.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_DatePicker(object):
    def setupUi(self, DatePicker):
        DatePicker.setObjectName("DatePicker")
        DatePicker.resize(640, 76)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(DatePicker)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(DatePicker)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.cboYear = QtWidgets.QComboBox(DatePicker)
        self.cboYear.setObjectName("cboYear")
        self.horizontalLayout.addWidget(self.cboYear)
        self.Month = QtWidgets.QLabel(DatePicker)
        self.Month.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.Month.setObjectName("Month")
        self.horizontalLayout.addWidget(self.Month)
        self.cboMonth = QtWidgets.QComboBox(DatePicker)
        self.cboMonth.setObjectName("cboMonth")
        self.horizontalLayout.addWidget(self.cboMonth)
        self.Day = QtWidgets.QLabel(DatePicker)
        self.Day.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.Day.setObjectName("Day")
        self.horizontalLayout.addWidget(self.Day)
        self.cboDay = QtWidgets.QComboBox(DatePicker)
        self.cboDay.setObjectName("cboDay")
        self.horizontalLayout.addWidget(self.cboDay)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(DatePicker)
        QtCore.QMetaObject.connectSlotsByName(DatePicker)

    def retranslateUi(self, DatePicker):
        _translate = QtCore.QCoreApplication.translate
        DatePicker.setWindowTitle(_translate("DatePicker", "Form"))
        self.label.setText(_translate("DatePicker", "Year"))
        self.Month.setText(_translate("DatePicker", "Month"))
        self.Day.setText(_translate("DatePicker", "Day"))
