import sys
import plotly.express as px
import pyqtgraph as pg
import matplotlib.pyplot as plt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from gui.mainWindow import Ui_mainWindow
from flimdata import flimdata
from fitting import fitter


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
        self.ptuFileHistory = []


        # Some random data for testing the pyqtgraph module
        self.hour = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.data = [32, 535, 64, 646, 757, 574, 457, 576, 546, 432]




        ''' GUI Actions '''
        self.updateLog('Setting up GUI actions...')

        # Close application
        self.actionQuit.triggered.connect(self.close)

        # Clear log
        self.pushButton_clearLog.pressed.connect(self.clearLog)

        # Load PTU file
        self.pushButton_LoadPTU.pressed.connect(self.loadPTUFile)

        # Show intensity image
        self.pushButton_showIntensityImage.pressed.connect(
            self.showIntensityImage)

        # Perform test fit
        self.pushButton_test.pressed.connect(self.testFit)

        # Show GUI
        self.show()
        self.updateLog('Finished initializing GUI. Ready for action...')





    def loadPTUFile(self):

        if self.flimObject:
            self.showError('Attention', 'Previously loaded data will be overwritten!')
            self.updateLog('Overwriting previous file...')
            self.flimObject = None

        filepath = QFileDialog.getOpenFileName(filter='PTU Files (*.ptu)')[0]

        # Reading spatial and temporal binning factors from GUI
        spatialBinning = self.spinBox_spatialBinning.value()
        temporalBinning = self.spinBox_temporalBinning.value()

        if filepath:
            self.flimObject = flimdata(
                filepath, spatialBinning, temporalBinning
            )
            self.ptuFileHistory.append(filepath)
            self.updateLog('Loaded' + filepath)
            self.lineEdit_filepath.setText(filepath)

        else:
            self.updateLog('No file selected.')

    def showIntensityImage(self):

        if self.flimObject is None:
            # Checking if ptu file has been loaded yet.
            self.showError('Loading Error', 'No FLIM data has been loaded yet!')
        else:
          #self.graphicsView.image(self.flimObject.intensityImage)
          pg.image(self.flimObject.intensityImage)


    def updateLog(self, logMessage: str):
        """Displays string on text box. Used as log for performed actions and potential errors. logMessage string is appended to list of strings in flimdata object --> logHistory
        Arguments:
            logMessage {str} -- Log text to be displayed.
        """   
        self.logHistory.append(logMessage)
        self.logConsole.appendPlainText(self.logHistory[-1])

    def clearLog(self):
        self.logHistory = []
        self.logConsole.clear()


    def showError(self, header: str, message: str):
        """Calls a Qt5 Message Box (critical) to attract users attention.
        Should be called from function, when a condition to run a certain action is not yet met, e.g. no file has been loaded etc. 
        
        Arguments:
            header {str} -- Window title of message box
            message {str} -- Message to be displayed in message box
        """        
        QMessageBox.critical(
            self,
            header,
            message
        )

    def testFit(self):
        fitObject = fitter(self.flimObject.flimarray, timeAxis = self.flimObject.timeAxis)

        testfit = fitObject.pixelwise_fit(photonthreshold = 1, rightcuttoff = 1)
        plt.imshow(testfit)
        plt.show()