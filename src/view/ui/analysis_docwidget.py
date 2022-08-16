# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/analysis_docwidget.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AnalysisDocWidget(object):
    def setupUi(self, AnalysisDocWidget):
        AnalysisDocWidget.setObjectName("AnalysisDocWidget")
        AnalysisDocWidget.resize(640, 480)
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.dockWidgetContents)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 1, 1, 1)
        self.lnName = QtWidgets.QLabel(self.dockWidgetContents)
        self.lnName.setObjectName("lnName")
        self.gridLayout.addWidget(self.lnName, 0, 1, 1, 1)
        self.txtName = QtWidgets.QLineEdit(self.dockWidgetContents)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 2, 1, 1)
        self.cboSegment = QtWidgets.QComboBox(self.dockWidgetContents)
        self.cboSegment.setObjectName("cboSegment")
        self.gridLayout.addWidget(self.cboSegment, 1, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cmdAuto = QtWidgets.QPushButton(self.dockWidgetContents)
        self.cmdAuto.setObjectName("cmdAuto")
        self.horizontalLayout.addWidget(self.cmdAuto)
        self.cmdSettings = QtWidgets.QPushButton(self.dockWidgetContents)
        self.cmdSettings.setObjectName("cmdSettings")
        self.horizontalLayout.addWidget(self.cmdSettings)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.tableView = QtWidgets.QTableView(self.dockWidgetContents)
        self.tableView.setObjectName("tableView")
        self.verticalLayout_2.addWidget(self.tableView)
        AnalysisDocWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(AnalysisDocWidget)
        QtCore.QMetaObject.connectSlotsByName(AnalysisDocWidget)

    def retranslateUi(self, AnalysisDocWidget):
        _translate = QtCore.QCoreApplication.translate
        AnalysisDocWidget.setWindowTitle(_translate("AnalysisDocWidget", "DockWidget"))
        self.label.setText(_translate("AnalysisDocWidget", "Riverscape segment"))
        self.lnName.setText(_translate("AnalysisDocWidget", "Analysis name"))
        self.cmdAuto.setText(_translate("AnalysisDocWidget", "Auto-Calculate"))
        self.cmdSettings.setText(_translate("AnalysisDocWidget", "Settings"))
