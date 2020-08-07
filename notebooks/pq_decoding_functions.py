
'''
PicoQuant TTTR / PTU File Decoding Functions
--------------------------------------------
Set of functions that are used to decode PicoQuant TTTR files and loading them into RAM.
For use with Jupyter Notebooks. Numba JIT accelerated.
For importing raw TTTR data into memory, use readPTUData(path = 'path/to/file.ptu') and provide the
path to the PTU file to be processed.
To turn
'''

# Importing modules
import sys, struct, io, os
import math
import numpy as np
from numba import jit
from numba.typed import List
import scipy.signal as signal
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize



## Record type and header type definitions
tyEmpty8      = struct.unpack(">i", bytes.fromhex("FFFF0008"))[0]
tyBool8       = struct.unpack(">i", bytes.fromhex("00000008"))[0]
tyInt8        = struct.unpack(">i", bytes.fromhex("10000008"))[0]
tyBitSet64    = struct.unpack(">i", bytes.fromhex("11000008"))[0]
tyColor8      = struct.unpack(">i", bytes.fromhex("12000008"))[0]
tyFloat8      = struct.unpack(">i", bytes.fromhex("20000008"))[0]
tyTDateTime   = struct.unpack(">i", bytes.fromhex("21000008"))[0]
tyFloat8Array = struct.unpack(">i", bytes.fromhex("2001FFFF"))[0]
tyAnsiString  = struct.unpack(">i", bytes.fromhex("4001FFFF"))[0]
tyWideString  = struct.unpack(">i", bytes.fromhex("4002FFFF"))[0]
tyBinaryBlob  = struct.unpack(">i", bytes.fromhex("FFFFFFFF"))[0]

rtHydraHarp2T3 = struct.unpack(">i", bytes.fromhex('01010304'))[0]


@jit(nopython=True, cache=True)
def treatOverflows(recordarray, macrotimefactor):
    '''
    Function treatOverflows(
    recordarray: 4 x numRec NumPy array holding raw 32 bit photon records in ['record']
    macrotimefactor: multiplication factor for mactotime clock to recover real experiment macrotime
    )
    Output is recordarray, but with populated ['macrotime'] row

    Takes whole record array and recovers real macrotime from raw photon TTTR data by adding
    number of macrotime clock overflows. See PicoQuant PTU documentary for further details and explanation.
    '''

    OVERFLOW_PERIOD = 1024
    overflow_cor = 0

    for record in recordarray:
        if(record['marker'] == 127):
            overflow_cor += OVERFLOW_PERIOD * \
                (record['record'] & (2**10 - 1))

        record['macrotime'] = (overflow_cor + np.bitwise_and(record['record'], 2**10-1)) * macrotimefactor

    return(recordarray)


def countLines(recordarray):
    numLineStart = np.sum(recordarray['marker'] == 65)
    numLineStop = np.sum(recordarray['marker'] == 66)

    if(numLineStart != numLineStop):
        print('Line start and line stop markers are not equal. Corrupted file?')

    return(numLineStart)


#@jit(nopython = True, cache = True)
def readPTUData(path: str, makeFLIMInfo: bool = True):
    """readPTUData()

    Arguments:
        path {str} -- Path to PicoQuant TTTR / PTU file to be processed
        makeFLIMInfo {bool} -- Make Python dictionary containing required infos for image reconstruction for quicker access-

    Output:
        macrotimes {np.ndarray} -- Array of macrotimes of TTTR file in Float32.
        nanotimes {np.ndarray} -- Array of nanotimes in Float32.
        markers {np.ndarray} -- Array of system / event marker signals in UInt32
        header_contents {KV-pair} -- Key-Value-Pair containing header section of TTTR file.
    """

    # Open file defined in ptupath
    ptureadstream = open(path, 'rb')

    # Checking file magic and version
    filemagic = ptureadstream.read(8).decode('utf8').strip('\0')

    if(filemagic != 'PQTTTR'):
        print('%s is not a .ptu file!' % path)
        ptureadstream.close()
    #else:
        #print('%s is a valid .ptu file... Commencing.' % ptupath)

    fileversion = ptureadstream.read(8).decode('utf8').strip('\0')
    #print('File Version: %s' % fileversion)


    ## Decoding Header
    ## setting up header end string to terminate header decoding in while loop
    headerend_tag = 'Header_End'
    reached_headerend = False


    # tuple that stores decoded information from header section
    header_contents = {}

    # decoding header
    while(reached_headerend == False):
        headerpiece = ptureadstream.read(48)
        tagId = headerpiece[0:32].decode('latin1').strip('\0') # Necessary for non-US computer systems (If I remember correcly..., otherwise utf-8 encoding)
        tagIdx = struct.unpack('<i', headerpiece[32:36])[0]
        tagType = struct.unpack('<i', headerpiece[36:40])[0]
        tagVal = headerpiece[40:48]

        if(tagId == headerend_tag):
            reached_headerend = True
            ptureadstream.read(4) # Offset required so that photon records (see second part) are 'in frame'!
            #print('Found Header_End.')
            break

        if(tagType == tyEmpty8):
            header_contents['Empty'] =  'Empty'

        elif(tagType == tyBool8):
            value = struct.unpack('<q', tagVal)[0]
            header_contents[tagId] =  value

        elif(tagType == tyInt8):
            value = struct.unpack('<q', tagVal)[0]
            header_contents[tagId] =  value

        elif(tagType == tyFloat8):
            value = struct.unpack('<d', tagVal)[0]
            header_contents[tagId] =  value

        elif(tagType == tyFloat8Array):
            value = struct.unpack("<q", tagVal)[0]
            #print('Float array with %d entries' % value / 8)

        elif(tagType == tyAnsiString):
            value = struct.unpack('<q', tagVal)[0]
            string = ptureadstream.read(value).decode('latin1').strip('\0')
            header_contents[tagId] =  string

        elif(tagType == tyWideString):
            value = struct.unpack('<q', tagVal)[0]
            string = ptureadstream.read(value).decode('utf-16-le').strip('\0')
            header_contents[tagId] =  string

        elif(tagType == tyBinaryBlob):
            value = struct.unpack("<q", tagVal)[0]
            header_contents[tagId] =  value

        elif(tagType == tyBitSet64):
            value = struct.unpack('<q', tagVal)[0]
            header_contents[tagId] =  value

        elif(tagType == tyColor8):
            value = struct.unpack('<q', tagVal)[0]
            header_contents[tagId] =  "{0:#0{1}x}".format(value,18)

        elif(tagType == tyBinaryBlob):
            value = struct.unpack('<q', tagVal)[0]
            header_contents[tagId] =  value

        elif(tagType == tyTDateTime):
            print('')

        else:
            continue
            #print('Unknown header tag type. Ignored.')


    headerend_bitoffset = ptureadstream.tell() # Needed to quickly jump to photon records instead of header

    #print('Finished decoding header.')

    # Copying header info into FLIMInfo dict

    try:
        FLIMInfo = {
            'Filename' : header_contents['$Filename'],
            'Comment': header_contents['$Comment'],
            'RecordType' : header_contents['TTResultFormat_TTTRRecType'],
            'BitsPerRecord' : header_contents['TTResultFormat_BitsPerRecord'],
            'PixelResolution' : header_contents['$ReqHdr_SpatialResolution'],
            'PixelsX' : header_contents['ImgHdr_PixX'],
            'PixelsY' : header_contents['ImgHdr_PixY'],
            'GlobalResolution' : header_contents['MeasDesc_GlobalResolution'],
            'BaseResolution' : header_contents['HW_BaseResolution'],
            'Resolution' : header_contents['MeasDesc_Resolution'],
            'BinningFactor' : header_contents['MeasDesc_BinningFactor'],
            'SyncRate' : header_contents['TTResult_SyncRate'],
            'NumberOfRecords': header_contents['TTResult_NumberOfRecords'],
            'LineStart': header_contents['ImgHdr_LineStart'],
            'LineStop': header_contents['ImgHdr_LineStop']
        }
    except:
        FLIMInfo = {
            #'Filename' : header_contents['$Filename'],
            #'Comment': header_contents['$Comment'],
            'RecordType' : header_contents['TTResultFormat_TTTRRecType'],
            'BitsPerRecord' : header_contents['TTResultFormat_BitsPerRecord'],
            #'PixelResolution' : header_contents['$ReqHdr_SpatialResolution'],
            'PixelsX' : header_contents['ImgHdr_PixX'],
            'PixelsY' : header_contents['ImgHdr_PixY'],
            'GlobalResolution' : header_contents['MeasDesc_GlobalResolution'],
            'BaseResolution' : header_contents['HW_BaseResolution'],
            'Resolution' : header_contents['MeasDesc_Resolution'],
            'BinningFactor' : header_contents['MeasDesc_BinningFactor'],
            'SyncRate' : header_contents['TTResult_SyncRate'],
            'NumberOfRecords': header_contents['TTResult_NumberOfRecords'],
            'LineStart': header_contents['ImgHdr_LineStart'],
            'LineStop': header_contents['ImgHdr_LineStop']
        }



    #print(FLIMInfo['LineStart'], FLIMInfo['LineStop'])
    # Closing read stream
    ptureadstream.close()


    # Reading photon records from ptu file, reopening read stream at headerend_bitoffset
    ## Initializing record array with pre-defined data types and length (read from header -> NumberOfRecords)
    recordBitType = np.dtype([('record', np.uint32), ('marker', np.uint8),
                                  ('nanotime', np.float64), ('macrotime', np.float64)])
    recordarray = np.zeros(
            shape=FLIMInfo['NumberOfRecords'] - 1, dtype=recordBitType)

    ## Getting macro and nano time conversion factors from FLIMInfo
    macroMultFactor = FLIMInfo['GlobalResolution']
    nanoMultFactor = FLIMInfo['Resolution'] * 1e9

    ## Dumping records into recordarray
    with open(path, 'rb') as file:
        file.seek(headerend_bitoffset)
        recordarray[:]['record'] = np.fromfile(file, dtype=np.uint32)
        file.close()

    ## Recover marker signals and nano times by bitwise operations on recordarray['record']
    recordarray[:]['marker'] = (np.right_shift(recordarray[:]['record'], 25) & 127)
    recordarray[:]['nanotime'] = ((np.right_shift(recordarray[:]['record'], 10) & 32767) * nanoMultFactor).astype(np.float64)

    # Recover macro times using treatOverflows()
    recordarray = treatOverflows(recordarray, macroMultFactor)

    header_contents = FLIMInfo
    header_contents['NumberOfLines'] = countLines(recordarray)
    header_contents['NumberOfFrames'] = int(header_contents['NumberOfLines'] / header_contents['PixelsX'])

    #macrotimes = np.array(recordarray['macrotime'], dtype = np.float32)
    #nanotimes = np.array(recordarray['nanotime'], dtype = np.float32)
    #markers = np.array(recordarray['marker'], dtype = np.uint8)



    return(recordarray, header_contents)


@jit(nopython = False, cache = True)
def sinCorr(correction_factor, number_of_pixels, pixel_mult_factor = 10):
    corrected_bins = np.linspace(-(correction_factor), (correction_factor), (pixel_mult_factor * number_of_pixels))
    np.sin(corrected_bins, corrected_bins)
    np.add(corrected_bins, np.max(corrected_bins), corrected_bins)
    np.multiply(corrected_bins, 1/np.max(corrected_bins), corrected_bins)
    np.multiply(corrected_bins, (number_of_pixels - 1), corrected_bins)

    return(corrected_bins, pixel_mult_factor)



@jit(nopython=True, cache=True)
def buildFLIMArray(
	recordarray,
	channel,
	linesinfile,
	pixelsx,
	pixelsy,
	globRes,
	timeRes,
	spatialBinning,
	temporalBinning,
	sinusodialCorr = 0.0):
    '''
    buildFLIMArray(
    - recordarray: 4 x numRec NumPy array, holds raw photon data and system events
    - channel: int; which channel to reconstruct the flimarray from
    - pixelsx: original image dimension in X, stored in FLIMInfo
    - pixelsy: original image dimension in Y, stored in FLIMInfo
    - globRes: global measurment of nanotime, stored in FLIMInfo, in ns, 51 ns for 20 MHz laser pulse frequency
    - timeRes: nanotime resolution of TCSPC device, in ps
    - spatialBinning: user-defined binning factor of image, calculated as 2**factor
    - temporalBinning: user-defined binning factor for fluorescence decay histogram
    )
    '''

    eventCounter = 0  # Keeps track of photon / marker events while looping through data
    lineCounter = 0  # Stores current scan line numbers
    frameCounter = 0  # Stores current frame number
    # How many frames are in the image; assume square format
    framesInFile = math.floor(linesinfile / pixelsx)

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

    # Generating array for sinosidial image correction using sinCorr() function
    # sinCorr() needs number of pixels and the correction factor, which specifies
    # what percentage of the sin curve is used for mapping of pixels and thus
    # correction of the distorted image
    # An excess of correction bins is produced and handeled as float (!), because due
    # to the distortion, some pixels will be rounded to other values and thus do not
    # map to an actual pixel in a particular line. Because of that,
    # sinCorr also returns the number of exceeding bins. This is the multiplier needed
    # to assign the pixel to the corrected bin
    corrected_bins, correction_mult_factor = sinCorr(
    	sinusodialCorr,
    	nPixelY,
    	pixel_mult_factor = 20
    )


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
                    diff = round(correction_mult_factor * ((tmpEvents[i] - lineStart)/pixelTime))
                    binID = math.floor((tmpNano[i]/globalResolution)*decayBins) - 1
                    pixelIDY = int(round(corrected_bins[int(diff)]))

                    if(pixelIDY < 0 or pixelIDY > (nPixelY - 1)):
                        #oorPhotons = oorPhotons + 1
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

        if (lineCounter > (pixelsx - 1)):
            frameCounter = frameCounter + 1
            pixelIDX = 0
            lineCounter = 0

        if(frameCounter >= framesInFile or eventCounter >= len(recordarray['marker'])):
            lastLine = True

        eventCounter += 1

    #print("Assigned photons to pixels.\n",
    #      (oorPhotons / np.sum(intensityImage))*100,
    #      "% of photons were out of range... Total:", oorPhotons, "of", np.sum(intensityImage), "photons.")

    return(flimarray, intensityImage)



@jit(nopython=True, cache=True)
def buildFrameArray(recordarray,
                    channel,
                    linesinfile,
                    pixelsx,
                    pixelsy,
                    globRes,
                    timeRes,
                    spatialBinning,
                    temporalBinning,
                    sinusodialCorr = 0.001):
    '''
    buildFrameArray
    Same as buildFLIMArray but instead of the 3D FLIM array (x-y-decay)
    it returns the individual frames from the TTTR data.
    (
    - recordarray: 4 x numRec NumPy array, holds raw photon data and system events
    - channel: int; which channel to reconstruct the flimarray from
    - pixelsx: original image dimension in X, stored in FLIMInfo
    - pixelsy: original image dimension in Y, stored in FLIMInfo
    - globRes: global measurment of nanotime, stored in FLIMInfo, in ns, 51 ns for 20 MHz laser pulse frequency
    - timeRes: nanotime resolution of TCSPC device, in ps
    - spatialBinning: user-defined binning factor of image, calculated as 2**factor
    - temporalBinning: user-defined binning factor for fluorescence decay histogram
    )
    '''

    eventCounter = 0  # Keeps track of photon / marker events while looping through data
    lineCounter = 0  # Stores current scan line numbers
    frameCounter = 0  # Stores current frame number
    # How many frames are in the image; assume square format
    framesInFile = math.floor(linesinfile / pixelsx)

    # Number of TCSPC bins based on time between pulses and TCSPC time resolution
    globalResolution = globRes * 10E8  # time between pulses in ns

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
    tmpMarker = 0  # Holds marker value for one loop iteration
    tmpMacro = 0  # Holds macrotime value for one loop iteration
    diff = 0  # Stores difference between photon macro time and line start to determine photon y-position
    # Count out-of-range photons (photons with macrotime below or above line time difference)
    oorPhotons = 0

    nPixelX = int(pixelsx / binningFactor)
    nPixelY = int(pixelsy / binningFactor)

    pixelIDX = 0  # Current x position in image
    pixelIDY = 0  # Current y position in image

    # Pre-allocating numpy array that hold individual frame scans
    # Instead of the third axis holding the decay axis, it now
    # holds the individual frame scan intensity images.
    intensity_image_array = np.zeros((nPixelX, nPixelY, framesInFile), dtype=np.uint16)

    corrected_bins, correction_mult_factor = sinCorr(
        sinusodialCorr,
        nPixelY,
        pixel_mult_factor = 20
    )

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

            if(tmpMarker == channel):
                tmpEvents.append(tmpMacro)
            elif(tmpMarker == 66):
                lineActive = False
                lineStop = tmpMacro
                pixelTime = (lineStop - lineStart) / (nPixelY)

                # Build intensity image and FLIM array from photon macro times
                for i in range(0, len(tmpEvents)):
                    diff = round(correction_mult_factor * ((tmpEvents[i] - lineStart)/pixelTime))
                    #binID = math.floor((tmpNano[i]/globalResolution) * decayBins) - 1
                    pixelIDY = int(round(corrected_bins[int(diff)]))

                    if(pixelIDY < 0 or pixelIDY > (nPixelY - 1)):
                        #oorPhotons = oorPhotons + 1
                        if(pixelIDY < 0):
                            pixelIDY = 0
                        elif(pixelIDY > (nPixelY - 1)):
                            pixelIDY = nPixelY - 1

                    intensity_image_array[math.floor(pixelIDX)][pixelIDY][frameCounter] += 1

                pixelIDX = pixelIDX + (1/binningFactor)
                lineCounter = lineCounter + 1
                tmpEvents = [np.float64(x) for x in range(0)]

            eventCounter += 1

        if (lineCounter > (pixelsx - 1)):
            frameCounter = frameCounter + 1
            pixelIDX = 0
            lineCounter = 0

        if(frameCounter >= framesInFile or eventCounter >= len(recordarray['marker'])):
            lastLine = True

        eventCounter += 1

    #print("Assigned photons to pixels.\n",
    #      (oorPhotons / np.sum(intensityImage))*100,
    #      "% of photons were out of range... Total:", oorPhotons, "of", np.sum(intensityImage), "photons.")

    return(intensity_image_array)



def make_time_axis(global_resolution, resolution, number_of_bins = 0):
    t_end = global_resolution * 1E12
    dt = resolution * 1E12

    if(number_of_bins == 0):
        number_of_bins = math.ceil(t_end / dt)

    t_axis = np.linspace(0, t_end, number_of_bins)

    return(t_axis)


def load_flim_data(
	path,
	channel = 0,
	spatialBinning = 0,
	temporalBinning = 0,
	sinusodial_correction = 0.001,
	makeFLIMInfo = True):
    '''
    Function wrapper for readPTUData and buildFLIMarray.
    Returns the 3D FLIM array and the intensity image of the ptu file provided with path (str).
    '''
    recordarray, header_info = readPTUData(path, makeFLIMInfo = makeFLIMInfo)
    header_info['LinesInFile'] = countLines(recordarray)

    flim_array, intensity_image = buildFLIMArray(
        recordarray = recordarray,
        channel = channel,
        linesinfile = header_info['LinesInFile'],
        pixelsx = header_info['PixelsX'],
        pixelsy = header_info['PixelsY'],
        globRes = header_info['GlobalResolution'],
        timeRes = header_info['Resolution'],
        spatialBinning = spatialBinning,
        temporalBinning = temporalBinning,
        sinusodialCorr = sinusodial_correction
    )

    time_axis = make_time_axis(
        header_info['GlobalResolution'],
        header_info['Resolution'],
        number_of_bins = flim_array.shape[2]
    )

    return(flim_array, intensity_image, time_axis)
