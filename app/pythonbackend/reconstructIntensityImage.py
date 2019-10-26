import numpy as np
import math
from numba import jit
import sys


@jit(nopython=True, cache=True)
def assignNanotimes(flimarray, channel, linesinfile, pixelsx, pixelsy):
    # assign nanotimes to 3D FLIM Image array
    # flimimage = np.zeros((FLIMInfo['PixelsX'],
    #                     FLIMInfo['PixelsY'],
    #                      round(FLIMInfo['GlobalResolution'] / FLIMInfo['BaseResolution'])),
    #                    dtype = (np.int8))

    eventCounter = 0 # Keeps track of photon / marker events while looping through data
    lineCounter = 0 # Stores current scan line numbers
    frameCounter = 0 # Stores current frame number
    framesInFile = linesinfile / pixelsx # How many frames are in the image; assume square format

    lineStart = 0
    lineStop = 0
    pixelTime = 0 # Tmp variable for storing time/pixel when line start and stop macro times are determined; needed to assign photons to y pixels in a line

    lastLine = False # Set to True when last scan line was evaluated and frameCounter >= framesInFile
    lineActive = False # Set to True when line start marker is found (= 65), starts photon assignments to y-pixels in a line (x); set to False when line stop marker is found (=66)

    tmpEvents = [np.float64(x) for x in range(0)] # List storing photon macrotimes when line is active to determine y-pixel position of photon
    tmpNano = [np.float64(x) for x in range(0)] # List storing photon nanotimes to assign to 3D-FLIM array in x-y position 
    tmpMarker = 0 # Holds marker value for one loop iteration
    tmpMacro = 0 # Holds macrotime value for one loop iteration
    tmpNanotime = 0 # Holds nanotime value for one loop iteration
    diff = 0 # Stores difference between photon macro time and line start to determine photon y-position
    oorPhotons = 0 # Count out-of-range photons (photons with macrotime below or above line time difference)

    pixelIDX = 0 # Current x position in image
    pixelIDY = 0 # Current y position in image

    intensityImage = np.zeros((pixelsx, pixelsy), dtype=np.int16) # 2D array for intensity image

    while(lastLine == False):
        tmpMarker = flimarray['marker'][eventCounter]

        if(tmpMarker == 65): # Event is line start marker
            lineActive = True # Starting line evaluation (next while loop)
            lineStart = flimarray['macrotime'][eventCounter] # Store line start time
            eventCounter += 1
            continue # Skip this loop iteration

        while(lineActive == True):
            tmpMarker = flimarray['marker'][eventCounter]
            tmpMacro = flimarray['macrotime'][eventCounter]
            tmpNanotime = flimarray['nanotime'][eventCounter]

            if(tmpMarker == channel):
                tmpEvents.append(tmpMacro)
                tmpNano.append(tmpNanotime)
            elif(tmpMarker == 66):
                lineActive = False
                lineStop = tmpMacro
                pixelTime = (lineStop - lineStart) / pixelsy

                for photon in tmpEvents:
                    diff = photon - lineStart
                    pixelIDY = math.floor(diff / pixelTime)

                    if(pixelIDY < 0 or pixelIDY > (pixelsy - 1)):
                        oorPhotons = oorPhotons + 1
                        if(pixelIDY < 0):
                            pixelIDY = 0
                        elif(pixelIDY > (pixelsy - 1)):
                            pixelIDY = pixelsy - 1

                    intensityImage[pixelIDX][pixelIDY] = intensityImage[pixelIDX][pixelIDY] + 1

                pixelIDX = pixelIDX + 1
                lineCounter = lineCounter + 1
                tmpEvents = [np.float64(x) for x in range(0)]
                tmpNano = [np.float64(x) for x in range(0)]

            eventCounter += 1

        if(lineCounter >= (pixelsx - 1)):
            frameCounter = frameCounter + 1
            pixelIDX = 0
            lineCounter = 0

        if(frameCounter >= framesInFile):
            lastLine = True
            #break

        eventCounter += 1



    print("Assigned photons to pixels.\n",
          (oorPhotons / np.sum(intensityImage))*100,
          "% of photons were out of range... Total:", oorPhotons, "of", np.sum(intensityImage), "photons.")



    return intensityImage

