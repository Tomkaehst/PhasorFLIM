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


def main():
    filepath = sys.argv[1]
    recordarray, FLIMInfo = reader.PTUReader(filepath)
    FLIMInfo['channelList'] = recon.checkChannelAvailability(recordarray)
    print("\nFLIMInfo: ", FLIMInfo, "\n")
    flimarray, intimage = recon.buildFLIMArray(recordarray,
                                     1,
                                     FLIMInfo['LinesInFile'],
                                     FLIMInfo['PixelsX'],
                                     FLIMInfo['PixelsY'],
                                     FLIMInfo['GlobalResolution'],
                                     FLIMInfo['Resolution'],
                                     2,
                                     4)
    plt.imshow(intimage, cmap="gray")
    plt.savefig("imgOutput/out.png")
    plt.show()

    plt.plot(flimarray[68][52][:])
    #plt.yscale("log")
    plt.savefig("imgOutput/decay.png")
    plt.show()
    # Image.open("out.png")


if(__name__ == '__main__'):
    main()
