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

# Importing PyQt5 Modules
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# Importing analysis script
#import PTUReader as reader
#import reconstructIntensityImage as recon
#import globalFitting as glFit
#import visualizationFunctions as vis
#import odefitting as ode
from flimdata import *

# Importing GUI scripts and modules
from gui.mainWindowInterface import Ui_mainWindowInterface



if(__name__ == '__main__'):
    app = QApplication([])
    app.setApplicationName('FLIM Analyser')

    window = Ui_mainWindowInterface()

    print('Executing Qt5 App...')
    app.exec_()

    #cliMain()

