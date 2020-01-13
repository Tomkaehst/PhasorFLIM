# import required third-party modules
import sys
import struct
import io
import os
import math
from scipy import optimize
import numpy as np
from numba import jit
import matplotlib.pyplot as plt
from PIL import Image

# Importing analysis script
import PTUReader as reader
import reconstructIntensityImage as recon
import globalFitting as glFit
import visualizationFunctions as vis
import odefitting as ode
from flimdata import *


# Importing GUI scripts and modules
import gui.phasorflim as gui
from PyQt5 import QtCore, QtGui, QtWidgets


def cliMain():
    testfile = '../../app/testData/Coumarin2P_1_1.ptu'

    test = flimdata(filepath=testfile, spatialBinning = 2, temporalBinning = 2)

    print(test.FLIMInfo['availableChannels'])

    test.showIntensityImage(test.FLIMInfo['availableChannels'])

    return(0)



if(__name__ == '__main__'):
    # Initializing GUI
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    ui = gui.Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    app.exec_()

    cliMain()

    sys.exit()
