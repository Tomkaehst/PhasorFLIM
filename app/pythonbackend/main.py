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
import reconstructIntensityImage as reconstruct


def main():
    filepath = "testData/EGFP_Cherry_Co_1_1.ptu"
    flimarray, FLIMInfo = reader.PTUReader(filepath)
    image = reconstruct.assignNanotimes(
        flimarray, 0, FLIMInfo['LinesInFile'], FLIMInfo['PixelsX'], FLIMInfo['PixelsY'])
    img = Image.fromarray(image, mode="L")
    #img.show()
    img.save("imgOutput/intImage.png")


if(__name__ == '__main__'):
    main()
