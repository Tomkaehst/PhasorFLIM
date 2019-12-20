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


def cliMain():
    # filepath = sys.argv[1]
    # recordarray, FLIMInfo = reader.PTUReader(filepath)
    # print("******************************")
    # FLIMInfo['channelList'] = recon.checkChannelAvailability(recordarray)
    # print("******************************")
    # print("\nFLIMInfo: ", FLIMInfo, "\n")
    # print("******************************")

    # channel = int(input("Select channel (integer): "))

    # spatialBin = int(input("Spatial Binning Factor (integer):"))
    # temporalBin = int(input("Temporal Binning Factor (integer):"))

    # flimarray, intimage = recon.buildFLIMArray(recordarray,
    #                                            channel,
    #                                            FLIMInfo['LinesInFile'],
    #                                            FLIMInfo['PixelsX'],
    #                                            FLIMInfo['PixelsY'],
    #                                            FLIMInfo['GlobalResolution'],
    #                                            FLIMInfo['Resolution'],
    #                                            spatialBin,
    #                                            temporalBin)
    # recordarray = None  # Dereferencing recordarray to save RAM space

    # vis.showIntensityImage(intimage, saveImage=False)

    # globalLifetime = glFit.globalTailFit(flimarray, FLIMInfo, showPlot=True)
    # lifetimeImage = glFit.pixelwiseSimpleDecay(
    #     flimarray, 250, 10, FLIMInfo['GlobalResolution'])

    # vis.showLifetimeImage(lifetimeImage, globalLifetime,
    #                       lowerLimit=1.5, upperLimit=3)

    # print("******************************")
    # print("\nOverall fluorescence lifetime:", globalLifetime, "ns.")
    # print("******************************")
    # print("\nTerminating script...\n")

    # ode.fitSimulatedDecay()

    testfile = sys.argv[1]

    test = flimdata(filepath = testfile)

    print(test.FLIMInfo['availableChannels'])

    test.showIntensityImage(test.FLIMInfo['availableChannels'])


    return(0)


if(__name__ == '__main__'):
    cliMain()

    sys.exit()
