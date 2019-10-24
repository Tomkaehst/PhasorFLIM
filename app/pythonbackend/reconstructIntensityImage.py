import numpy as np
import math
from numba import jit


@jit(nopython=True, cache=True)
def assignNanotimes(flimarray, channel, linesinfile, pixelsx, pixelsy):
    # assign nanotimes to 3D FLIM Image array
    # flimimage = np.zeros((FLIMInfo['PixelsX'],
    #                     FLIMInfo['PixelsY'],
    #                      round(FLIMInfo['GlobalResolution'] / FLIMInfo['BaseResolution'])),
    #                    dtype = (np.int8))

    eventCounter = int(0)
    lineCounter = 0
    frameCounter = 0
    framesInFile = linesinfile / pixelsx

    pixelTime = 0

    lineStart = 0
    lineStop = 0

    lastLine = False
    lineActive = False

    tmpEvents = [np.float64(x) for x in range(0)]
    tmpNano = [np.float64(x) for x in range(0)]
    tmpMarker = 0
    tmpMacro = 0
    tmpNanotime = 0
    diff = 0

    pixelIDX = 0
    pixelIDY = 0

    intensityImage = np.zeros((pixelsx, pixelsy), dtype=np.int16)

    while(lastLine == False):
        tmpMarker = flimarray['marker'][eventCounter]

        if(tmpMarker == 65):
            lineActive = True
            lineStart = flimarray['macrotime'][eventCounter]
            eventCounter = eventCounter + 1
            # continue

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

                    if(pixelIDY < 0 or pixelIDY > (pixelIDY - 1)):
                        #print("Photon out of image range!")
                        if(pixelIDY < 0):
                            pixelIDY = 0
                        elif(pixelIDY > (pixelsy - 1)):
                            pixelIDY = pixelsy - 1

                    intensityImage[pixelIDX][pixelIDY] = intensityImage[pixelIDX][pixelIDY] + 1

                pixelIDX = pixelIDX + 1
                lineCounter = lineCounter + 1
                tmpEvents = [np.float64(x) for x in range(0)]
                tmpNano = [np.float64(x) for x in range(0)]

            eventCounter = eventCounter + 1

        eventCounter = eventCounter + 1

        if(lineCounter >= (pixelsx - 1)):
            #print("Finished scanning frame %d", frameCounter)
            frameCounter = frameCounter + 1
            pixelIDX = 0
            lineCounter = 0

        if(frameCounter >= framesInFile):
            lastLine = True
            break

    return intensityImage
