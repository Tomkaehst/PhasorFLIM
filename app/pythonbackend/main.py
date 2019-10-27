import sys
import struct
import io
import os
import math
import numpy as np
from numba import jit
import matplotlib.pyplot as plt
from PIL import Image

import PTUReader as reader
import reconstructIntensityImage as recon
import globalFitting as glFit


def main():
    filepath = sys.argv[1]
    recordarray, FLIMInfo = reader.PTUReader(filepath)
    print("******************************")
    FLIMInfo['channelList'] = recon.checkChannelAvailability(recordarray)
    print("******************************")
    print("\nFLIMInfo: ", FLIMInfo, "\n")
    flimarray, intimage = recon.buildFLIMArray(recordarray,
                                               0,
                                               FLIMInfo['LinesInFile'],
                                               FLIMInfo['PixelsX'],
                                               FLIMInfo['PixelsY'],
                                               FLIMInfo['GlobalResolution'],
                                               FLIMInfo['Resolution'],
                                               0,
                                               4)
    recordarray = None
    plt.imshow(intimage, cmap="gray")
    plt.savefig("imgOutput/out.png")
    plt.show()

    # plt.plot(flimarray[100][120][:])
    # plt.yscale("log")
    # plt.savefig("imgOutput/decay.png")
    # plt.show()

    lifetime = glFit.globalTailFit(flimarray, FLIMInfo)

    print("******************************")
    print("\nOverall fluorescence lifetime:", lifetime, "ns.")
    print("******************************")
    print("\nTerminating script...\n")


if(__name__ == '__main__'):
    main()
