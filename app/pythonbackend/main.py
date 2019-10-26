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
    filepath = "testData/BaseName_3_1.ptu"
    flimarray, FLIMInfo = reader.PTUReader(filepath)
    image = recon.reconstructImage(
        flimarray, 0, FLIMInfo['LinesInFile'], FLIMInfo['PixelsX'], FLIMInfo['PixelsY'])
    plt.imshow(image, cmap="inferno")
    plt.savefig("imgOutput/out.png")
    # Image.open("out.png")


if(__name__ == '__main__'):
    main()
