import sys
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
        self.flimObjects = []
        self.ptuFileHistory: List[str] = []


        # GUI Actions
        print('Setting up GUI actions...')

        ## Close application
        self.actionQuit.triggered.connect(self.close)

        ## Load PTU file
        self.btnLoadPTU.pressed.connect(self.loadPTUFile)


        # Show GUI
        print('Finished initializing GUI. Ready for action...')
        self.show()



    def loadPTUFile(self):

        filepath = QFileDialog.getOpenFileName(filter = 'PTU Files (*.ptu)')
        print('You have selected', filepath)


