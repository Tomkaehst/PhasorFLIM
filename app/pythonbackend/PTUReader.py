import struct
import sys
import io
import os
import json
import numpy as np
from numba import jit


print("Start decoding PTU script...\n")


# Setting up header and record type(s)
# Identifiers for data contained within header section of .ptu file
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

rtHydraHarp2T3 = struct.unpack(">i", bytes.fromhex('01010304'))[0]

# Setting up file reading
filepath = sys.argv[1]
filereadstream = open(filepath, 'rb')

filemagic = filereadstream.read(8).decode('utf8').strip('\0')

# Checking if .ptu file is loaded by file magic sequence
if(filemagic != 'PQTTTR'):
    print("Provided file is not a PicoQuant TTTR file...\nFile Path: %s" % filepath)
    filereadstream.close()
    sys.exit("Invalid file provided.")

fileversion = filereadstream.read(8).decode('utf8').strip('\0')

print('Start decoding "%s" TTTR file.\nValid .ptu file\nCommencing...' % filepath)


# Reading Header
# Setting up tuple for header and while loop for byte-wise reading
 
headerend_tag = 'Header_End'
reached_headerend = False
header_contents = {}

# Decoding header and storing header chunks in header_contents. Header information accessible by addressing header_contents['header_tag_id']. See PicoQuant header documentary (https://github.com/PicoQuant/PicoQuant-Time-Tagged-File-Format-Demos?files=1)

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
        string = filereadstream.read(value).decode('latin1').strip('\0')
        header_contents[tagId] = string

    elif(tagType == tyWideString):
        value = struct.unpack('<q', tagVal)[0]
        string = filereadstream.read(value).decode('utf-16-le').strip('\0')
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


# File byte offset after Header_End. Saved for numpy later on.
headerend_bitoffset = filereadstream.tell()

# Getting important information for FLIM image reconstruction
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


# Reading photon data into (typed) numpy array

# First closing old header read stream (this can probably be done better in future -> File Stream approach!)

# Numba accelerated function definition for overflow treatment

# Keep in here! Significantly increases speed of overflow correction!
@jit(nopython=True)
def treatOverflows(recordarray, macrotimefactor):
    overflow_period = 1024
    overflow_cor = 0

    for record in recordarray:
        if(record['marker'] == 127):
            overflow_cor = overflow_cor + overflow_period * \
                (record['record'] & (2 ^ 10 - 1))

        record['macrotime'] = overflow_cor + \
            ((record['record'] & 1023) * macrotimefactor)

    return(recordarray)


# Initializing typed numpy array for raw photon records (UInt32) and decoded infos (marker: UInt8, nanotime: float64, macrotime: float64)
recordBitType = np.dtype([('record', np.uint32), ('marker', np.uint8),
                          ('nanotime', np.float64), ('macrotime', np.float64)])

flimarray = np.zeros(
    shape=FLIMInfo['NumberOfRecords'] - 1, dtype=recordBitType)

# Calculating factors to recover true macrotime and nanotime from raw photon records stored in flimarray['record]
# Multiply with truensync to get experiment macro time
macroMultFactor = FLIMInfo['GlobalResolution']
nanoMultFactor = FLIMInfo['Resolution'] * 1e9


# Closing old readstream and opening new one for numpy
filereadstream.close()

with open(filepath, 'rb') as file:
    file.seek(headerend_bitoffset)
    flimarray[:]['record'] = np.fromfile(file, dtype=np.uint32)
    file.close()

# Recovering markers and nanotimes from raw photon records by applying right bitshift to flimarray
flimarray[:]['marker'] = np.right_shift(flimarray[:]['record'], 25)
flimarray[:]['nanotime'] = np.right_shift(
    flimarray[:]['record'], 10) * nanoMultFactor

# Recover macrotimes and treat overflows by calling treatOverflows()
treatOverflows(flimarray, macroMultFactor)

print("Read and recovered raw photon data from %s" % filepath)


sys.stdout.flush()
