# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui/phasorflim.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        mainWindow.setObjectName("mainWindow")
        mainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(mainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton_LoadPTU = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_LoadPTU.setGeometry(QtCore.QRect(40, 10, 111, 21))
        self.pushButton_LoadPTU.setObjectName("pushButton_LoadPTU")
        self.plotArea = QtWidgets.QGraphicsView(self.centralwidget)
        self.plotArea.setGeometry(QtCore.QRect(100, 120, 581, 421))
        self.plotArea.setObjectName("plotArea")
        self.label_channel = QtWidgets.QLabel(self.centralwidget)
        self.label_channel.setGeometry(QtCore.QRect(280, 10, 67, 17))
        self.label_channel.setObjectName("label_channel")
        self.label_spatialBinning = QtWidgets.QLabel(self.centralwidget)
        self.label_spatialBinning.setGeometry(QtCore.QRect(240, 30, 101, 17))
        self.label_spatialBinning.setObjectName("label_spatialBinning")
        self.label_temporalBinning = QtWidgets.QLabel(self.centralwidget)
        self.label_temporalBinning.setGeometry(QtCore.QRect(220, 50, 121, 17))
        self.label_temporalBinning.setObjectName("label_temporalBinning")
        self.spinBox_channel = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBox_channel.setGeometry(QtCore.QRect(370, 10, 48, 21))
        self.spinBox_channel.setMaximum(3)
        self.spinBox_channel.setObjectName("spinBox_channel")
        self.spinBox_spatialBinning = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBox_spatialBinning.setGeometry(QtCore.QRect(370, 30, 48, 21))
        self.spinBox_spatialBinning.setMaximum(8)
        self.spinBox_spatialBinning.setObjectName("spinBox_spatialBinning")
        self.spinBox_temporalBinning = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBox_temporalBinning.setGeometry(QtCore.QRect(370, 50, 48, 21))
        self.spinBox_temporalBinning.setMaximum(8)
        self.spinBox_temporalBinning.setObjectName("spinBox_temporalBinning")
        self.pushButton_showIntensityImage = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_showIntensityImage.setGeometry(QtCore.QRect(560, 20, 161, 25))
        self.pushButton_showIntensityImage.setObjectName("pushButton_showIntensityImage")
        mainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(mainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        mainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(mainWindow)
        self.statusbar.setObjectName("statusbar")
        mainWindow.setStatusBar(self.statusbar)
        self.actionQuit = QtWidgets.QAction(mainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.menuFile.addAction(self.actionQuit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(mainWindow)
        QtCore.QMetaObject.connectSlotsByName(mainWindow)

    def retranslateUi(self, mainWindow):
        _translate = QtCore.QCoreApplication.translate
        mainWindow.setWindowTitle(_translate("mainWindow", "MainWindow"))
        self.pushButton_LoadPTU.setText(_translate("mainWindow", "Load PTU File"))
        self.label_channel.setText(_translate("mainWindow", "Channel"))
        self.label_spatialBinning.setText(_translate("mainWindow", "Spatial Binning"))
        self.label_temporalBinning.setText(_translate("mainWindow", "Temporal Binning"))
        self.pushButton_showIntensityImage.setText(_translate("mainWindow", "Show Intensity Image"))
        self.menuFile.setTitle(_translate("mainWindow", "File"))
        self.actionQuit.setText(_translate("mainWindow", "Quit"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    ui = Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec_())

