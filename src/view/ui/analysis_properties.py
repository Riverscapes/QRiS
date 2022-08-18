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
        self.gridLayout = QtWidgets.QGridLayout(AnalysisProperties)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(AnalysisProperties)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.gridLayout.addWidget(self.tabWidget, 3, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(AnalysisProperties)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(AnalysisProperties)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.comboBox = QtWidgets.QComboBox(AnalysisProperties)
        self.comboBox.setObjectName("comboBox")
        self.verticalLayout.addWidget(self.comboBox)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout.addLayout(self.gridLayout_2)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(AnalysisProperties)
        QtCore.QMetaObject.connectSlotsByName(AnalysisProperties)

    def retranslateUi(self, AnalysisProperties):
        _translate = QtCore.QCoreApplication.translate
        AnalysisProperties.setWindowTitle(_translate("AnalysisProperties", "Analysis Properties"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("AnalysisProperties", "test"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("AnalysisProperties", "Tab 2"))
        self.label.setText(_translate("AnalysisProperties", "TextLabel"))
