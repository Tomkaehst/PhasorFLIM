from PyQt5 import QtCore, QtGui, QtWidgets
import gui.phasorflim as guiLogic

class Ui_mainWindowInterface(guiLogic):
    def __init__(self):
        super(guiLogic, self).__init__()

        # History of loaded PTU files
        self.ptuFileHistory = []

        # GUI Actions
        ## Load PTU file
        self.loadPTUFile_Action = QtWidgets.QAction('&Load PTU...')
        self.loadPTUFile_Action.triggered.connect(self.loadPTUFile)        


    def loadPTUFile(self, filepath: string = None):
        print("Lol")
