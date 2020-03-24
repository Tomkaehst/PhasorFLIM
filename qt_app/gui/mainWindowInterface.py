import sys
import pyqtgraph as pg
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
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

        # Initializing ROI objects
        self.ROI = None
        self.selectedDecay = None

        self.logHistory = []

        # Setting up flimdata class
        self.flimObject = None
        self.ptupath = None
        self.ptuFileHistory = []


        ''' GUI Actions '''
        self.updateLog('Setting up GUI actions...')

        # Close application
        self.actionQuit.triggered.connect(self.close)

        # Clear log
        self.pushButton_clearLog.pressed.connect(self.clearLog)

        # Load PTU file
        self.pushButton_selectFile.pressed.connect(self.selectFile)
        self.pushButton_LoadPTU.pressed.connect(self.loadPTUFile)

        # Show intensity image
        self.pushButton_showIntensityImage.pressed.connect(
            self.showIntensityImage
        )

        # Show ROI-selected decay
        self.pushButton_showSelectedDecay.pressed.connect(
            self.showSelectedDecay
        )
        
        # Perform test fit
        self.pushButton_fitSelection.pressed.connect(self.testFit)

        # Show GUI
        self.show()
        self.updateLog('Finished initializing GUI. Ready for action...')




    def selectFile(self):
        if self.flimObject:
            self.showError('Attention', 'Previously loaded data will be overwritten!')
            self.updateLog('Overwriting previous file...')
            self.flimObject = None
        
        self.ptupath = QFileDialog.getOpenFileName(filter='PTU Files (*.ptu)')[0]
        self.lineEdit_filepath.setText(self.ptupath)
        self.ptuFileHistory.append(self.ptupath)

    def loadPTUFile(self):
        # Reading spatial and temporal binning factors from GUI
        spatialBinning = self.spinBox_spatialBinning.value()
        temporalBinning = self.spinBox_temporalBinning.value()

        print(spatialBinning, temporalBinning)

        filepath = self.ptupath

        if filepath:
            self.progressBar.setMaximum(0) # setMaximum used, because when max and min of progress bar are equal, it shows 'busy'
            self.flimObject = flimdata(
                filepath, spatialBinning, temporalBinning
            )
            self.ptuFileHistory.append(filepath)
            self.updateLog('Loaded' + filepath)
            self.graphicsView_decay.clear()
            self.graphicsView_decay.plot(
                x = self.flimObject.timeAxis,
                y = self.flimObject.overallDecays
            )
            self.progressBar.setMaximum(1)

        else:
            self.updateLog('No file selected.')

    def showIntensityImage(self):

        if self.flimObject is None:
            # Checking if ptu file has been loaded yet.
            self.showError('Loading Error', 'No FLIM data has been loaded yet!')
        else:
            self.graphicsView_intensityimage.addItem(pg.ImageItem(self.flimObject.intensityImage))
            self.tabWidget_view.setCurrentIndex(0)
            
            


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

    def showSelectedDecay(self):
        if(self.flimObject):
            if(self.ROI is None):
                self.ROI = pg.ROI(
                    [self.flimObject.intensityImage.shape[0]/ 2, self.flimObject.intensityImage.shape[1]/ 2],
                    [20, 20]
                )
                self.graphicsView_intensityimage.addItem(self.ROI)
            else:
                coordinates = self.ROI.pos()
                size = self.ROI.size()
                
                self.selectedDecay = np.sum(np.sum(
                    self.flimObject.flimarray[int(coordinates[0]):int(coordinates[0] + size[0]), int(coordinates[1]):int(coordinates[1] + size[1]), :], axis = 0
                ), axis = 0)

                self.graphicsView_decay.clear()
                self.graphicsView_decay.plot(
                    x = self.flimObject.timeAxis,
                    y = self.selectedDecay
                )
                self.tabWidget_view.setCurrentIndex(1)
            
        else:
            self.showError('Selection not possible.', 'Please load a FLIM file first.')





    def testFit(self):
        if(self.flimObject):
            fitObject = fitter(self.flimObject.flimarray, timeAxis = self.flimObject.timeAxis)
            self.showError('Starting fitting procedure...', 'Starting the fitting procedure. This might take a while. Application is unresponsive during fitting...')
            testfit = fitObject.fit_summed_decay()

            self.graphicsView_decay.clear()
            self.graphicsView_decay.plot(
                x = self.flimObject.timeAxis,
                y = self.flimObject.overallDecays
            )
            self.graphicsView_decay.plot(
                x = self.flimObject.timeAxis,
                y = testfit
            )
        else:
            self.showError('Fitting not possible.', 'Please load a FLIM file first.')
