import sys
import plotly.express as px
import pyqtgraph as pg
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from gui.mainWindow import Ui_mainWindow
from flimdata import flimdata


class Ui_mainWindowInterface(QMainWindow, Ui_mainWindow):

    def __init__(self, *args, **kwargs):

        # Inheriting Ui_mainWindow and initializung GUI
        print('Starting GUI...')
        super(Ui_mainWindowInterface, self).__init__(*args, **kwargs)
        print('Setting up Ui_mainWindow...')
        self.setupUi(self)

        self.logHistory = []

        # Setting up flimdata class
        self.flimObject = None
        self.ptuFileHistory: List[str] = []

        self.hour = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.data = [32, 535, 64, 646, 757, 574, 457, 576, 546, 432]

        # GUI Actions
        print('Setting up GUI actions...')

        # Close application
        self.actionQuit.triggered.connect(self.close)

        # Load PTU file
        self.pushButton_LoadPTU.pressed.connect(self.loadPTUFile)

        # Show intensity image
        self.pushButton_showIntensityImage.pressed.connect(
            self.showIntensityImage)

        # Show GUI
        self.show()
        self.updateLog('Finished initializing GUI. Ready for action...')

    def loadPTUFile(self):

        filepath = QFileDialog.getOpenFileName(filter='PTU Files (*.ptu)')[0]

        # Reading spatial and temporal binning factors from GUI
        spatialBinning = self.spinBox_spatialBinning.value()
        temporalBinning = self.spinBox_temporalBinning.value()

        if filepath:
            self.flimObject = flimdata(
                filepath, spatialBinning, temporalBinning)
            self.ptuFileHistory.append(filepath)
            self.updateLog('Loading PTU file.')
            self.lineEdit_filepath.setText(filepath)

        else:
            self.updateLog('No file selected.')

    def showIntensityImage(self):
        if self.flimObject is None:
            QMessageBox.critical(
                self, 'Info', 'No FLIM data has been loaded yet!'
            )
            return
        else:
          #self.graphicsView.image(self.flimObject.intensityImage)
          pg.image(self.flimObject.intensityImage)

    def tabTestButton(self):
        self.updateLogprint("LOL!")

    def updateLog(self, logMessage):
        self.logHistory.append(logMessage)
        self.logConsole.appendPlainText(self.logHistory[-1])
