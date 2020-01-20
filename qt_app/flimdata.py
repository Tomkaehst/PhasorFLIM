import sys
import os
import io
import struct
import math
import matplotlib.pyplot as plt
import numpy as np
from numba import jit
from numba.typed import List


class flimdata:
    def __init__(self, filepath: str, spatialBinning: int, temporalBinning: int):
        """[summary]

        Arguments:
            filepath {str} -- [description]
            spatialBinning {int} -- [description]
            temporalBinning {int} -- [description]
        """

        self.filepath = filepath
        self.spatialBinning = spatialBinning
        self.temporalBinning = temporalBinning

        # Defining data types for the raw record array where ptu data stream is written in to
        self.recordarrayDataTypes = np.dtype([('record', np.uint32), ('marker', np.uint8),
                                              ('nanotime', np.float64), ('macrotime', np.float64)])

        self.FLIMInfo = None  # Quick access FLIM image infos
        self.header_contents = None  # Whole file header
        # Bit offset of file in filepath, where TTTR records start
        self.headerBitOffset = None

        # Reading header; do this automatically when flimdata instance is created; no great time pennalty
        self.readPTUHeader(self.filepath)

        # Loading photon data into recordarray
        self.recordarray = self.readPhotonData(
            self.filepath, self.headerBitOffset, self.FLIMInfo['NumberOfRecords']
        )

        # Generating nano time axis
        self.timeAxis = self.generateNanotimeaxis()

        # Getting list of channels from the data
        self.FLIMInfo['availableChannels'] = self.checkChannelAvailability(
            self.recordarray)

        # Counting line events, requires for image reconstruction
        self.FLIMInfo['LinesInFile'] = self.countLines(self.recordarray)

        # Calculating intensity image for all available channels
        self.intensityImage = self.reconstructIntensityImage(
            self.recordarray,
            self.FLIMInfo['availableChannels'][0],
            self.FLIMInfo['LinesInFile'],
            self.FLIMInfo['PixelsX'],
            self.FLIMInfo['PixelsY']
        )

        # Generating overall decay histograms from available channels
        #self.overallDecays = self.overallDecay()

    def readPTUHeader(self, filepath):
        """[summary]

        Arguments:
            filepath {[type]} -- [description]
        """

        # Setting up header and record types
        tyEmpty8 = struct.unpack(">i", bytes.fromhex("FFFF0008"))[0]
        tyBool8 = struct.unpack(">i", bytes.fromhex("00000008"))[0]
        tyInt8 = struct.unpack(">i", bytes.fromhex("10000008"))[0]
        tyBitSet64 = struct.unpack(">i", bytes.fromhex("11000008"))[0]
        tyColor8 = struct.unpack(">i", bytes.fromhex("12000008"))[0]
        tyFloat8 = struct.unpack(">i", bytes.fromhex("20000008"))[0]
        tyTDateTime = struct.unpack(">i", bytes.fromhex("21000008"))[0]
        tyFloat8Array = struct.unpack(">i", bytes.fromhex("2001FFFF"))[0]
        tyAnsiString = struct.unpack(">i", bytes.fromhex("4001FFFF"))[0]
        tyWideString = struct.unpack(">i", bytes.fromhex("4002FFFF"))[0]
        tyBinaryBlob = struct.unpack(">i", bytes.fromhex("FFFFFFFF"))[0]

        rtHydraHarp2T3 = struct.unpack(">i", bytes.fromhex('01010304'))[
            0]  # Only coding for HydraHarp V2 TTTR data

        # Setting up file reading
        filereadstream = open(self.filepath, 'rb')

        # Checking first 8 bytes for correct file magic
        filemagic = filereadstream.read(8).decode('utf8').strip('\0')
        if(filemagic != 'PQTTTR'):
            print('%s is not a valid PTU file. Aborting.' % self.filepath)
            exit(0)

        # Reading Header
        # Setting up tuple for header contents and stop condition variable for exiting the whole loop
        headerend_tag = 'Header_End'
        reached_headerend = False
        header_contents = {}

        while(reached_headerend == False):
            headerpiece = filereadstream.read(48)
            # Necessary for non-US computer systems (If I remember correcly..., otherwise utf-8 encoding)
            tagId = headerpiece[0:32].decode('latin1').strip('\0')
            tagIdx = struct.unpack('<i', headerpiece[32:36])[0]
            tagType = struct.unpack('<i', headerpiece[36:40])[0]
            tagVal = headerpiece[40:48]

            if(tagId == headerend_tag):
                reached_headerend = True
                # Offset required so that photon records (see second part) are 'in frame'!
                filereadstream.read(4)
                break

            if(tagType == tyEmpty8):
                header_contents['Empty'] = 'Empty'

            elif(tagType == tyBool8):
                value = struct.unpack('<q', tagVal)[0]
                header_contents[tagId] = value

            elif(tagType == tyInt8):
                value = struct.unpack('<q', tagVal)[0]
                header_contents[tagId] = value

            elif(tagType == tyFloat8):
                value = struct.unpack('<d', tagVal)[0]
                header_contents[tagId] = value

            elif(tagType == tyFloat8Array):
                value = struct.unpack("<q", tagVal)[0]

            elif(tagType == tyAnsiString):
                value = struct.unpack('<q', tagVal)[0]
                string = filereadstream.read(
                    value).decode('latin1').strip('\0')
                header_contents[tagId] = string

            elif(tagType == tyWideString):
                value = struct.unpack('<q', tagVal)[0]
                string = filereadstream.read(
                    value).decode('utf-16-le').strip('\0')
                header_contents[tagId] = string

            elif(tagType == tyBinaryBlob):
                value = struct.unpack("<q", tagVal)[0]
                header_contents[tagId] = value

            elif(tagType == tyBitSet64):
                value = struct.unpack('<q', tagVal)[0]
                header_contents[tagId] = value

            elif(tagType == tyColor8):
                value = struct.unpack('<q', tagVal)[0]
                header_contents[tagId] = "{0:#0{1}x}".format(value, 18)

            elif(tagType == tyBinaryBlob):
                value = struct.unpack('<q', tagVal)[0]
                header_contents[tagId] = value

            elif(tagType == tyTDateTime):
                continue

            else:
                continue
                # print('Unknown header tag type. Ignored.')

        # Getting current position of readstream; used later to quickly jump to position in file where photon records start
        headerend_bitoffset = filereadstream.tell()
        self.headerBitOffset = filereadstream.tell()

        # Reading header contents into FLIMInfo dict for quick access
        # - Filename: Filename
        # - Comment: String containing user comments
        # - TTResultsFormat_TTTRRecType: Type of the photon records i.e. which device was used
        # - TTResultFormat_BitsPerRecord: Number of bits in a photon record
        # - ReqHdr_SpatialResolution: Width of a pixel in micrometer
        # - ImgHdr_PixX: How many pixels in X?
        # - ImgHdr_PixY: How many pixels in Y?
        # - MeasDesc_GlobalResolution: time resolution of measurement
        # - HW_BaseResolution: Principal time resolution of device
        # - MeasDesc_Resolution: TCSPC resolution, also obtained by BaseResolution * BinningFactor
        # - MeasDesc_BinningFactor: Binning factor
        # - TTResult_SyncRate: Laser pulse / Sync rate of measurement
        # - TTResult_NumberOfRecords: How many 32 bit records in file?
        FLIMInfo = {
            'Filename': header_contents['$Filename'],
            'Comment': header_contents['$Comment'],
            'RecordType': header_contents['TTResultFormat_TTTRRecType'],
            'BitsPerRecord': header_contents['TTResultFormat_BitsPerRecord'],
            'PixelResolution': header_contents['$ReqHdr_SpatialResolution'],
            'PixelsX': header_contents['ImgHdr_PixX'],
            'PixelsY': header_contents['ImgHdr_PixY'],
            'GlobalResolution': header_contents['MeasDesc_GlobalResolution'],
            'BaseResolution': header_contents['HW_BaseResolution'],
            'Resolution': header_contents['MeasDesc_Resolution'],
            'BinningFactor': header_contents['MeasDesc_BinningFactor'],
            'SyncRate': header_contents['TTResult_SyncRate'],
            'NumberOfRecords': header_contents['TTResult_NumberOfRecords']
        }

        # Check if photon records from loaded ptu can be read and processed
        if (FLIMInfo['RecordType'] != rtHydraHarp2T3):
            raise Exception(
                "Loaded PTU file is not from HydraHarp V2 TTTR. Other photon record types are not implemented yet!")

        self.FLIMInfo = FLIMInfo
        self.header_contents = header_contents

        # Closing file readstream
        filereadstream.close()

    # @jit(nopython = True, cache = True)

    def readPhotonData(self, filepath: str, bitoffset: int, numRecords: int):
        """[summary]

        Arguments:
            filepath {string} -- [description]
            bitoffset {int} -- [description]
            numRecords {int} -- [description]
        """

        # Initializing recordarray
        recordarray = np.zeros(shape=numRecords - 1,
                               dtype=self.recordarrayDataTypes)

        # Reading data from file into recordarray
        with open(filepath, 'rb') as file:
            file.seek(bitoffset)
            recordarray[:]['record'] = np.fromfile(file, dtype=np.uint32)
            file.close()

        '''
        Recovering marker and nanotime events from ['record'] array via bitwise operations on whole record array
        ---------------------------------------------------
        ['record'] holds a 32 bit uint.
        Marker values are extracted by bitwise right shift and readout of the first 8 bits.
            First bit is special bit. If it is set, the record is not a photon event but a system event.
        '''
        nanoMultFactor = self.FLIMInfo['Resolution'] * 1e9
        macroMultFactor = self.FLIMInfo['GlobalResolution']

        recordarray['marker'] = (np.right_shift(
            recordarray[:]['record'], 25) & 127)
        recordarray['nanotime'] = (np.right_shift(
            recordarray[:]['record'], 10) & 322767) * nanoMultFactor
        recordarray = self.treatOverflows(recordarray, macroMultFactor)

        return(recordarray)

    '''
    In order to use Numba in a class method, the method needs to be defined as static.
    This means, that it has no direct access to self and all arguments need to be explicitly passed
    to that function.
    '''
    @staticmethod
    @jit(nopython=True, cache=True)
    def treatOverflows(recordarray: np.ndarray, macrotimefactor: float):
        """[summary]

        Arguments:
            recordarray {np.ndarray} -- [description]
            macrotimefactor {float} -- [description]
        """

        overflow_period = 1024
        overflow_correction = 0

        for record in recordarray:
            if(record['marker'] == 127):  # All bits in a record set = macro time overflow
                overflow_correction += overflow_period * \
                    (record['record'] & (2**10 - 1))

            record['macrotime'] = (
                overflow_correction + np.bitwise_and(record['record'], 2**10 - 1)) * macrotimefactor

        return(recordarray)

    @staticmethod
    @jit(nopython=True, cache=True)
    def countLines(recordarray: np.ndarray):
        """
        Counts number of line start (marker == 65) and line stop (marker == 66) events in raw photon data marker stream.
        Uneven number indicates corrupted file.

        Arguments:
            recordarray {np.ndarray} -- 4 x numpy array, ['records'] - raw photon bit data; ['macrotime'] - system event time array, ['nanotime'] - nanotimes of photon events, ['marker'] - system markers
        """

        numLineStart = np.sum(recordarray['marker'] == 65)
        numLineStop = np.sum(recordarray['marker'] == 66)

        if(numLineStart != numLineStop):
            print(
                'Number of line start and line stop markers does not match. File may be corrupted.'
            )

        return(numLineStart, numLineStop)

    # @jit(nopython=True, cache=True)
    def checkChannelAvailability(self, recordarray: np.ndarray):
        """[summary]

        Arguments:
            recordarray {np.ndarray} -- [description]
        """

        # Initialized as numba.typed.List, because Python lists will be deprecated in future Numba versions
        channelList = List()

        if(np.any(recordarray['marker'] == 0)):
            channelList.append(0)
        if(np.any(recordarray['marker'] == 1)):
            channelList.append(1)
        if(np.any(recordarray['marker'] == 2)):
            channelList.append(2)
        if(np.any(recordarray['marker'] == 3)):
            channelList.append(3)

        return(channelList)

    @staticmethod
    @jit(nopython=True, cache=True)
    def reconstructIntensityImage(recordarray: np.ndarray, channel: int, linesinfile: int, pixelsx: int, pixelsy: int):
        '''
            Function sums photons detected in an image in order to reconstruct the intensity image from the TTTR data.
        '''

        eventCounter = 0  # Keeps track of photon / marker events while looping through data
        lineCounter = 0  # Stores current scan line numbers
        frameCounter = 0  # Stores current frame number
        # How many frames are in the image; assume square format
        # linesinfile has two element, we only use the first one, because we assume a square image
        framesInFile = linesinfile[0] / pixelsx

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
        tmpMacro = 0  # Holds macrotime value for one loop
        tmpNanotime = 0  # Holds nanotime value for one loop iteration
        diff = 0  # Stores difference between photon macro time and line start to determine photon y-position
        # Count out-of-range photons (photons with macrotime below or above line time difference)
        oorPhotons = 0

        pixelIDX = 0  # Current x position in image
        pixelIDY = 0  # Current y position in image

        # 2D array of arrays for intensity image, as many arrays as elements in channelList

        #intensityImages = []

        # for channel in channelList:
        #    temp = np.zeros((pixelsx, pixelsy), dtype = np.int16)
        #    intensityImages.append(temp)

        #channel = 0

        intensityImage = np.zeros((pixelsx, pixelsy), dtype=np.int16)

        while(lastLine == False):
            tmpMarker = recordarray['marker'][eventCounter]

            if(tmpMarker == 65):  # Event is line start marker
                lineActive = True  # Starting line evaluation (next while loop)
                # Store line start time
                lineStart = recordarray['macrotime'][eventCounter]
                eventCounter += 1
                continue  # Skip this loop iteration

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

        return(intensityImage)

    def showIntensityImage(self, channel: int, color_palette: str = None, interpolation_method: str = None):
        """[summary]

        Arguments:
            channel {int} -- [description]

        Keyword Arguments:
            color_palette {str} -- [description] (default: {None})
            interpolation_method {str} -- [description] (default: {None})
        """

        if color_palette is None:
            color_palette = 'gray_r'

        if interpolation_method is None:
            interpolation_method = 'bessel'

        plt.imshow(self.intensityImage, cmap=color_palette,
                   interpolation=interpolation_method)
        plt.show()

    def generateNanotimeaxis(self):
        tEnd = self.FLIMInfo['GlobalResolution'] * \
            1E12  # Converting to picoseconds
        dt = self.FLIMInfo['Resolution'] * 1E12
        nBins = math.ceil((tEnd / dt))
        tAxis = np.linspace(0, tEnd, nBins)
        return(tAxis)

    @staticmethod
    @jit
    def overallDecay(self):
        """[summary]

        Arguments:
            recordarray {np.array} -- [description]
            channelList {List[int]} -- [description]
        """

        decays = []

        print(self.FLIMInfo['availableChannels'])

        for channel in self.FLIMInfo['availableChannels']:
            temp = np.histogram(
                self.recordarray['macrotimes'][np.where(self.recordarray['marker'] == channel)], bins=self.timeAxis.size)
            decays.append(temp)

        return(0)
