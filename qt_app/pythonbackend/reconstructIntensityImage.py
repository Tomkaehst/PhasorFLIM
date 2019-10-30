import numpy as np
import math
from numba import jit
import sys


@jit(nopython=True, cache=True)
def reconstructImage(recordarray, channel, linesinfile, pixelsx, pixelsy):
    '''
    Function: reconstructImage(recordarray, channel, linesinfile, pixelsx, pixelsy) -> intensityImage [2D NumPy array; pixelsx x pixelsy]
    - recordarray [4D numpy array; record, marker, nanotime, macrotime]: TTTR data produced by PTUReader.py.PTUReader(path), macrotime overflows corrected
    - channel [int]: channel ID that should be used for image reconstruction, 0 to 3 for channels 1 to 4
    - linesinfile [int]: from FLIMInfo['LinesInFile] produces by PTUReader.py.countLines(recordarray), indicates number of line markers in TTTR data
    - pixelsx [int]: from FLIMInfo produced by PTUReader.PTUReader(), image dimension in X
    - pixelsy [int]: image dimension in Y
    '''

    eventCounter = 0  # Keeps track of photon / marker events while looping through data
    lineCounter = 0  # Stores current scan line numbers
    frameCounter = 0  # Stores current frame number
    # How many frames are in the image; assume square format
    framesInFile = linesinfile / pixelsx

    lineStart = 0
    lineStop = 0
    pixelTime = 0  # Tmp variable for storing time/pixel when line start and stop macro times are determined; needed to assign photons to y pixels in a line

    # Set to True when last scan line was evaluated and frameCounter >= framesInFile
    lastLine = False
    # Set to True when line start marker is found (= 65), starts photon assignments to y-pixels in a line (x); set to False when line stop marker is found (=66)
    lineActive = False

    # List storing photon macrotimes when line is active to determine y-pixel position of photon
    tmpEvents = [np.float64(x) for x in range(0)]
    # List storing photon nanotimes to assign to 3D-FLIM array in x-y position
    tmpNano = [np.float64(x) for x in range(0)]
    tmpMarker = 0  # Holds marker value for one loop iteration
    tmpMacro = 0  # Holds macrotime value for one loop iteration
    tmpNanotime = 0  # Holds nanotime value for one loop iteration
    diff = 0  # Stores difference between photon macro time and line start to determine photon y-position
    # Count out-of-range photons (photons with macrotime below or above line time difference)
    oorPhotons = 0

    pixelIDX = 0  # Current x position in image
    pixelIDY = 0  # Current y position in image

    # 2D array for intensity image
    intensityImage = np.zeros((pixelsx, pixelsy), dtype=np.int16)

    while(lastLine == False):
        tmpMarker = recordarray['marker'][eventCounter]

        if(tmpMarker == 65):  # Event is line start marker
            lineActive = True  # Starting line evaluation (next while loop)
            # Store line start time
            lineStart = recordarray['macrotime'][eventCounter]
            eventCounter += 1
            continue  # Skip this loop iteration

        if(tmpMarker == 0 or tmpMarker == 1 or tmpMarker == 2 or tmpMarker == 3):
            oorPhotons += 1

        while(lineActive == True):
            tmpMarker = recordarray['marker'][eventCounter]
            tmpMacro = recordarray['macrotime'][eventCounter]
            tmpNanotime = recordarray['nanotime'][eventCounter]

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

        if(lineCounter > (pixelsx - 1)):
            frameCounter = frameCounter + 1
            pixelIDX = 0
            lineCounter = 0

        if(frameCounter >= framesInFile):
            lastLine = True

        eventCounter += 1

    print("Assigned photons to pixels.\n",
          (oorPhotons / np.sum(intensityImage))*100,
          "% of photons were out of range... Total:", oorPhotons, "of", np.sum(intensityImage), "photons.")

    return intensityImage

@jit(nopython=True, cache=True)
def checkChannelAvailability(recordarray):

    channelList = []

    if(np.any(recordarray['marker'] == 0)):
        channelList.append(0)

    if(np.any(recordarray['marker'] == 1)):
        channelList.append(1)

    if(np.any(recordarray['marker'] == 2)):
        channelList.append(2)

    if(np.any(recordarray['marker'] == 3)):
        channelList.append(3)

    print("Detected channels: ", channelList)

    return channelList


@jit(nopython=True, cache=True)
def buildFLIMArray(recordarray, channel, linesinfile, pixelsx, pixelsy, globRes, timeRes, spatialBinning, temporalBinning):
    '''
    Function: buildFLIMArray(
        recordarray:
        channel:
        linesinfile:
        pixelsx:
        pixelsy:
        globRes:
        timeRes:
        spatialBinning:
        temporalBinning:
    )
    '''

    eventCounter = 0  # Keeps track of photon / marker events while looping through data
    lineCounter = 0  # Stores current scan line numbers
    frameCounter = 0  # Stores current frame number
    # How many frames are in the image; assume square format
    framesInFile = linesinfile / pixelsx
    # Number of TCSPC bins based on time between pulses and TCSPC time resolution
    decayBins = math.ceil((globRes / timeRes)/(2**temporalBinning))
    globalResolution = globRes * 10E8  # time between pulses in ns
    timeResolution = timeRes * 10E9  # TCSPC time resolution in nss

    binningFactor = 2**spatialBinning

    lineStart = 0
    lineStop = 0
    pixelTime = 0  # Tmp variable for storing time/pixel when line start and stop macro times are determined; needed to assign photons to y pixels in a line

    # Set to True when last scan line was evaluated and frameCounter >= framesInFile
    lastLine = False
    # Set to True when line start marker is found (= 65), starts photon assignments to y-pixels in a line (x); set to False when line stop marker is found (=66)
    lineActive = False

    # List storing photon macrotimes when line is active to determine y-pixel position of photon
    tmpEvents = [np.float64(x) for x in range(0)]
    # List storing photon nanotimes to assign to 3D-FLIM array in x-y position
    tmpNano = [np.float64(x) for x in range(0)]
    tmpMarker = 0  # Holds marker value for one loop iteration
    tmpMacro = 0  # Holds macrotime value for one loop iteration
    tmpNanotime = 0  # Holds nanotime value for one loop iteration
    diff = 0  # Stores difference between photon macro time and line start to determine photon y-position
    # Count out-of-range photons (photons with macrotime below or above line time difference)
    oorPhotons = 0

    nPixelX = int(pixelsx / binningFactor)
    nPixelY = int(pixelsy / binningFactor)

    pixelIDX = 0  # Current x position in image
    pixelIDY = 0  # Current y position in image

    flimarray = np.zeros((nPixelX, nPixelY, decayBins), dtype=np.uint16)
    # 2D array for intensity image
    intensityImage = np.zeros((nPixelX, nPixelY), dtype=np.uint16)

    while(lastLine == False):
        tmpMarker = recordarray['marker'][eventCounter]

        if(tmpMarker == 65):  # Event is line start marker
            lineActive = True  # Starting line evaluation (next while loop)
            # Store line start time
            lineStart = recordarray['macrotime'][eventCounter]
            eventCounter += 1
            continue  # Skip this loop iteration

        if(tmpMarker == 0 or tmpMarker == 1 or tmpMarker == 2 or tmpMarker == 3):
            oorPhotons += 1

        while(lineActive == True):
            tmpMarker = recordarray['marker'][eventCounter]
            tmpMacro = recordarray['macrotime'][eventCounter]
            tmpNanotime = recordarray['nanotime'][eventCounter]

            if(tmpMarker == channel):
                tmpEvents.append(tmpMacro)
                tmpNano.append(tmpNanotime)
            elif(tmpMarker == 66):
                lineActive = False
                lineStop = tmpMacro
                pixelTime = (lineStop - lineStart) / (nPixelY)

                # Build intensity image and FLIM array from photon macro times
                for i in range(0, len(tmpEvents)):
                    diff = tmpEvents[i] - lineStart
                    pixelIDY = math.floor(diff / pixelTime)
                    binID = math.floor((tmpNano[i]/globalResolution)*decayBins)

                    if(pixelIDY < 0 or pixelIDY > nPixelY):
                        oorPhotons = oorPhotons + 1
                        if(pixelIDY < 0):
                            pixelIDY = 0
                        elif(pixelIDY > (nPixelY - 1)):
                            pixelIDY = nPixelY - 1

                    intensityImage[math.floor(pixelIDX)][pixelIDY] += 1
                    flimarray[math.floor(pixelIDX)][pixelIDY][binID] += 1

                pixelIDX = pixelIDX + (1/binningFactor)
                lineCounter = lineCounter + 1
                tmpEvents = [np.float64(x) for x in range(0)]
                tmpNano = [np.float64(x) for x in range(0)]

            eventCounter += 1

        if(lineCounter > (pixelsx - 1)):
            frameCounter = frameCounter + 1
            pixelIDX = 0
            lineCounter = 0

        if(frameCounter >= framesInFile):
            lastLine = True

        eventCounter += 1

    print("Assigned photons to pixels.\n",
          (oorPhotons / np.sum(intensityImage))*100,
          "% of photons were out of range... Total:", oorPhotons, "of", np.sum(intensityImage), "photons.")

    return flimarray, intensityImage
