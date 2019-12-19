import sys
import os
import io
import struct
import math
import numpy as np
from numba import jit


class flimdata(object):

    def __init__(self, filepath):
        # super().__init__()
        self.filepath = filepath
        self.spatialBinning = None
        self.temporalBinning = None
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
        self.timeAxis = self.generateNanotimeaxis(self.FLIMInfo)

        # Getting list of channels from the data
        self.FLIMInfo['availableChannels'] = self.checkChannelAvailability(
            self.recordarray)

        # Generating overall decay histograms from available channels
        self.overallDecays = self.overallDecay(
            self.recordarray, self.FLIMInfo['availableChannels']
        )

    def readPTUHeader(self, filepath):

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

        self.FLIMInfo = FLIMInfo
        self.header_contents = header_contents

        # Closing file readstream
        filereadstream.close()

        return(0)

    # @jit(nopython = True, cache = True)

    def readPhotonData(self, filepath, bitoffset, numRecords):
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

    # @jit(nopython = True, cache = True)

    @staticmethod
    @jit(nopython=True, cache=True)
    def treatOverflows(recordarray, macrotimefactor):
        '''
            Description:
                - 
        '''

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
    def countLines(recordarray):
        '''
            Description:
                Counts number of line start (marker == 65) and line stop (marker == 66) events in raw photon data marker stream.
                Uneven number indicates corrupted file.
            Input Argument:
                recordarray: 4 x numpy array, ['records'] - raw photon bit data; ['macrotime'] - system event time array, ['nanotime'] - nanotimes of photon events, ['marker'] - system markers
        '''
        numLineStart = np.sum(recordarray['marker'] == 65)
        numLineStop = np.sum(recordarray['marker'] == 66)

        if(numLineStart != numLineStop):
            print(
                'Number of line start and line stop markers does not match. File may be corrupted.')

        return(numLineStart, numLineStop)

    # @jit(nopython=True, cache=True)
    def checkChannelAvailability(self, recordarray):
        '''
            Checks for which channels events were detected in photon data stream.
        '''

        channelList = []

        if(np.any(recordarray['marker'] == 0)):
            channelList.append(0)
        if(np.any(recordarray['marker'] == 1)):
            channelList.append(1)
        if(np.any(recordarray['marker'] == 2)):
            channelList.append(2)
        if(np.any(recordarray['marker'] == 3)):
            channelList.append(3)

        return(channelList)

    def generateNanotimeaxis(self, FLIMInfo):
        tEnd = FLIMInfo['GlobalResolution'] * 1E12  # Converting to picoseconds
        dt = FLIMInfo['Resolution'] * 1E12
        nBins = math.ceil((tEnd / dt))
        t = np.linspace(0, tEnd, nBins)
        return(t)

    def overallDecay(self, recordarray, channelList):

        overallDecays = np.ndarray((len(channelList, max(self.timeAxis))))

        for channel in channelList:
            overallDecays[channelList] = np.sum(recordarray[])
        return(0)
