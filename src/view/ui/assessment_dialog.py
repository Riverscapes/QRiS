# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/assessment_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_assessment_dialog(object):
    def setupUi(self, assessment_dialog):
        assessment_dialog.setObjectName("assessment_dialog")
        assessment_dialog.resize(304, 293)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("/Users/philip/code/riverscapes/QRiS/src/view/ui/experimental/../../../../../../../../../../../icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        assessment_dialog.setWindowIcon(icon)
        self.label = QtWidgets.QLabel(assessment_dialog)
        self.label.setGeometry(QtCore.QRect(20, 20, 231, 16))
        self.label.setObjectName("label")
        self.plainTextEdit_assessment_description = QtWidgets.QPlainTextEdit(assessment_dialog)
        self.plainTextEdit_assessment_description.setGeometry(QtCore.QRect(20, 130, 261, 111))
        self.plainTextEdit_assessment_description.setObjectName("plainTextEdit_assessment_description")
        self.label_2 = QtWidgets.QLabel(assessment_dialog)
        self.label_2.setGeometry(QtCore.QRect(20, 100, 181, 16))
        self.label_2.setObjectName("label_2")
        self.dateEdit_assessment_date = QtWidgets.QDateEdit(assessment_dialog)
        self.dateEdit_assessment_date.setGeometry(QtCore.QRect(20, 50, 161, 21))
        self.dateEdit_assessment_date.setCalendarPopup(True)
        self.dateEdit_assessment_date.setDate(QtCore.QDate(2021, 12, 21))
        self.dateEdit_assessment_date.setObjectName("dateEdit_assessment_date")
        self.pushButton_save_assessment = QtWidgets.QPushButton(assessment_dialog)
        self.pushButton_save_assessment.setGeometry(QtCore.QRect(160, 250, 113, 32))
        self.pushButton_save_assessment.setObjectName("pushButton_save_assessment")
        self.pushButton_cancel_assessment = QtWidgets.QPushButton(assessment_dialog)
        self.pushButton_cancel_assessment.setGeometry(QtCore.QRect(20, 250, 113, 32))
        self.pushButton_cancel_assessment.setObjectName("pushButton_cancel_assessment")

        self.retranslateUi(assessment_dialog)
        QtCore.QMetaObject.connectSlotsByName(assessment_dialog)

    def retranslateUi(self, assessment_dialog):
        _translate = QtCore.QCoreApplication.translate
        assessment_dialog.setWindowTitle(_translate("assessment_dialog", "Structure Assessment"))
        self.label.setText(_translate("assessment_dialog", "Assessment Date"))
        self.plainTextEdit_assessment_description.setPlaceholderText(_translate("assessment_dialog", "Notes about your assessment....."))
        self.label_2.setText(_translate("assessment_dialog", "Assessment Description"))
        self.dateEdit_assessment_date.setDisplayFormat(_translate("assessment_dialog", "MM/dd/yyyy"))
        self.pushButton_save_assessment.setText(_translate("assessment_dialog", "Save"))
        self.pushButton_cancel_assessment.setText(_translate("assessment_dialog", "Cancel"))
