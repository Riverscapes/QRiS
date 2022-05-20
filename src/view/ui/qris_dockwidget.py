# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/philip/code/riverscapes/QRiS/src/view/ui/qris_dockwidget.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_QRiSDockWidget(object):
    def setupUi(self, QRiSDockWidget):
        QRiSDockWidget.setObjectName("QRiSDockWidget")
        QRiSDockWidget.resize(489, 536)
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout = QtWidgets.QGridLayout(self.dockWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.treeView = QtWidgets.QTreeView(self.dockWidgetContents)
        self.treeView.setSortingEnabled(True)
        self.treeView.setHeaderHidden(True)
        self.treeView.setObjectName("treeView")
        self.treeView.header().setSortIndicatorShown(False)
        self.gridLayout.addWidget(self.treeView, 0, 0, 1, 1)
        QRiSDockWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(QRiSDockWidget)
        QtCore.QMetaObject.connectSlotsByName(QRiSDockWidget)

    def retranslateUi(self, QRiSDockWidget):
        _translate = QtCore.QCoreApplication.translate
        QRiSDockWidget.setWindowTitle(_translate("QRiSDockWidget", "QRiS"))
