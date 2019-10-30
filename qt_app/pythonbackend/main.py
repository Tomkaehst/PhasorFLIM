# import required third-party modules
import sys
import struct
import io
import os
import math
import numpy as np
from numba import jit
import matplotlib.pyplot as plt
from PIL import Image

# GUI
from PyQt5 import QtCore, QtGui, QtWidgets


# Importing analysis script
import PTUReader as reader
import reconstructIntensityImage as recon
import globalFitting as glFit
import visualizationFunctions as vis

class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        mainWindow.setObjectName("mainWindow")
        mainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(mainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.btnLoadPTU = QtWidgets.QPushButton(self.centralwidget)
        self.btnLoadPTU.setGeometry(QtCore.QRect(50, 40, 111, 21))
        self.btnLoadPTU.setObjectName("btnLoadPTU")
        self.ViewArea = QtWidgets.QGraphicsView(self.centralwidget)
        self.ViewArea.setGeometry(QtCore.QRect(100, 120, 581, 421))
        self.ViewArea.setObjectName("ViewArea")
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
        self.btnLoadPTU.setText(_translate("mainWindow", "Load PTU File"))
        self.label_channel.setText(_translate("mainWindow", "Channel"))
        self.label_spatialBinning.setText(_translate("mainWindow", "Spatial Binning"))
        self.label_temporalBinning.setText(_translate("mainWindow", "Temporal Binning"))
        self.menuFile.setTitle(_translate("mainWindow", "File"))
        self.actionQuit.setText(_translate("mainWindow", "Quit"))


# App Logic

def cliMain():
    filepath = sys.argv[1]
    recordarray, FLIMInfo = reader.PTUReader(filepath)
    print("******************************")
    FLIMInfo['channelList'] = recon.checkChannelAvailability(recordarray)
    print("******************************")
    print("\nFLIMInfo: ", FLIMInfo, "\n")
    print("******************************")

    channel = int(input("Select channel (integer): "))

    flimarray, intimage = recon.buildFLIMArray(recordarray,
                                               channel,
                                               FLIMInfo['LinesInFile'],
                                               FLIMInfo['PixelsX'],
                                               FLIMInfo['PixelsY'],
                                               FLIMInfo['GlobalResolution'],
                                               FLIMInfo['Resolution'],
                                               2,
                                               4)
    recordarray = None
    plt.imshow(intimage, cmap="gray")
    plt.savefig("imgOutput/out.png")
    plt.show()

    lifetime = glFit.globalTailFit(flimarray, FLIMInfo, showPlot = False)
    lifetimeImage = glFit.pixelwiseSimpleDecay(flimarray, 100, 10,FLIMInfo['GlobalResolution'])

    plt.imshow(lifetimeImage, cmap = "cubehelix")
    plt.text(10, 10, lifetime)
    plt.clim(1, 3)
    plt.colorbar()
    plt.show()


    print("******************************")
    print("\nOverall fluorescence lifetime:", lifetime, "ns.")
    print("******************************")
    print("\nTerminating script...\n")

if(__name__ == '__main__'):
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    ui = Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    app.exec_()
    cliMain()

    sys.exit()
