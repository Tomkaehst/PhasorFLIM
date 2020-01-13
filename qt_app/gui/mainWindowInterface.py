import sys
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import plotly.express as px
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from gui.phasorflim import Ui_mainWindow
from flimdata import flimdata

class Ui_mainWindowInterface(QMainWindow, Ui_mainWindow):

    def __init__(self, *args, **kwargs):

        # Inheriting Ui_mainWindow and initializung GUI
        print('Inheriting Ui_mainWindow class...')
        super(Ui_mainWindowInterface, self).__init__(*args, **kwargs)
        print('Setting up Ui_mainWindow...')
        self.setupUi(self)

        # Setting up flimdata class
        self.flimObject = None
        self.ptuFileHistory: List[str] = []

        self.hour = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.data = [32, 535, 64, 646, 757, 574, 457, 576, 546, 432]


        # GUI Actions
        print('Setting up GUI actions...')

        ## Close application
        self.actionQuit.triggered.connect(self.close)

        ## Load PTU file
        self.pushButton_LoadPTU.pressed.connect(self.loadPTUFile)

        ## Show intensity image
        self.pushButton_showIntensityImage.pressed.connect(self.showIntensityImage)

        # Show GUI
        print('Finished initializing GUI. Ready for action...')
        self.show()



    def loadPTUFile(self):

        filepath = QFileDialog.getOpenFileName(filter = 'PTU Files (*.ptu)')[0]

        # Reading spatial and temporal binning factors from GUI
        spatialBinning = self.spinBox_spatialBinning.value()
        temporalBinning = self.spinBox_temporalBinning.value()

        if filepath:
            self.flimObject = flimdata(filepath, spatialBinning, temporalBinning)
            self.ptuFileHistory.append(filepath)
            print('Loading PTU file', filepath), '...'

        else:
            print('No file selected.')


    def showIntensityImage(self):
        fig = px.scatter(x = self.hour, y = self.data)
        fig.show()



