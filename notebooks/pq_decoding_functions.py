
'''
PicoQuant TTTR / PTU File Decoding Functions
--------------------------------------------
Set of functions that are used to decode PicoQuant TTTR files and loading them into RAM.
For use with Jupyter Notebooks. Numba JIT accelerated.
For importing raw TTTR data into memory, use read_ptu_data(path = 'path/to/file.ptu') and provide the
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


# @jit(nopython=True, cache=True)
# def treat_overflows(recordarray, macrotimefactor):
#     '''
#     Function treat_overflows(
#     recordarray: 4 x numRec NumPy array holding raw 32 bit photon records in ['record']
#     macrotimefactor: multiplication factor for mactotime clock to recover real experiment macrotime
#     )
#     Output is recordarray, but with populated ['macrotime'] row

#     Takes whole record array and recovers real macrotime from raw photon TTTR data by adding
#     number of macrotime clock overflows. See PicoQuant PTU documentary for further details and explanation.
#     '''

#     OVERFLOW_PERIOD = 1024
#     overflow_cor = 0

#     for record in recordarray:
#         if(record['marker'] == 127):
#             overflow_cor += OVERFLOW_PERIOD * \
#                 (record['record'] & (2**10 - 1))

#         record['macrotime'] = (overflow_cor + np.bitwise_and(record['record'], 2**10-1)) * macrotimefactor

#     return(recordarray)


def treat_overflows(recordarray: np.array, macrotime_factor: float, overflow_period: int = 1024):
    '''
    Function treat_overflows(
    recordarray: 4 x numRec NumPy array holding raw 32 bit photon records in ['record']
    macrotimefactor: multiplication factor for mactotime clock to recover real experiment macrotime
    )
    Output is recordarray, but with populated ['macrotime'] row

    Takes whole record array and recovers real macrotime from raw photon TTTR data by adding
    number of macrotime clock overflows. See PicoQuant PTU documentary for further details and explanation.
    '''

    overflow_correction = 0

    for record in recordarray:
        # Overflow indicated by all marker bits set
        if record['marker'] == 127:
            # Getting number of overflows since experiment start
            # is written in macrotime field in case of overflow
            overflow_correction += overflow_period * np.bitwise_and(record['record'], (2**10 - 1))

        # Get macrotime from macrotime field and correcting overflow
        record['macrotime'] = (
            overflow_correction + np.bitwise_and(record['record'], (2**10 - 1))
        )

    return(recordarray['macrotime'])


def count_lines(recordarray, line_start: int = 65, line_stop: int = 66):
    numLineStart = np.sum(recordarray['marker'] == line_start)
    numLineStop = np.sum(recordarray['marker'] == line_stop)

    if(numLineStart != numLineStop):
        print('Line start and line stop markers are not equal. Corrupted file?')

    return(numLineStart)


# #@jit(nopython = True, cache = True)
# def read_ptu_data(path: str, makeFLIMInfo: bool = True):
#     """read_ptu_data()
#
#     Arguments:
#         path {str} -- Path to PicoQuant TTTR / PTU file to be processed
#         makeFLIMInfo {bool} -- Make Python dictionary containing required infos for image reconstruction for quicker access-
#
#     Output:
#         macrotimes {np.ndarray} -- Array of macrotimes of TTTR file in Float32.
#         nanotimes {np.ndarray} -- Array of nanotimes in Float32.
#         markers {np.ndarray} -- Array of system / event marker signals in UInt32
#         header_contents {KV-pair} -- Key-Value-Pair containing header section of TTTR file.
#     """
#
#     # Open file defined in ptupath
#     ptureadstream = open(path, 'rb')
#
#     # Checking file magic and version
#     filemagic = ptureadstream.read(8).decode('utf8').strip('\0')
#
#     if(filemagic != 'PQTTTR'):
#         print('%s is not a .ptu file!' % path)
#         ptureadstream.close()
#     #else:
#         #print('%s is a valid .ptu file... Commencing.' % ptupath)
#
#     fileversion = ptureadstream.read(8).decode('utf8').strip('\0')
#     #print('File Version: %s' % fileversion)
#
#
#     ## Decoding Header
#     ## setting up header end string to terminate header decoding in while loop
#     headerend_tag = 'Header_End'
#     reached_headerend = False
#
#
#     # tuple that stores decoded information from header section
#     header_contents = {}
#
#     # decoding header
#     while(reached_headerend == False):
#         headerpiece = ptureadstream.read(48)
#         tagId = headerpiece[0:32].decode('latin1').strip('\0') # Necessary for non-US computer systems (If I remember correcly..., otherwise utf-8 encoding)
#         tagIdx = struct.unpack('<i', headerpiece[32:36])[0]
#         tagType = struct.unpack('<i', headerpiece[36:40])[0]
#         tagVal = headerpiece[40:48]
#
#         if(tagId == headerend_tag):
#             reached_headerend = True
#             ptureadstream.read(4) # Offset required so that photon records (see second part) are 'in frame'!
#             #print('Found Header_End.')
#             break
#
#         if(tagType == tyEmpty8):
#             header_contents['Empty'] =  'Empty'
#
#         elif(tagType == tyBool8):
#             value = struct.unpack('<q', tagVal)[0]
#             header_contents[tagId] =  value
#
#         elif(tagType == tyInt8):
#             value = struct.unpack('<q', tagVal)[0]
#             header_contents[tagId] =  value
#
#         elif(tagType == tyFloat8):
#             value = struct.unpack('<d', tagVal)[0]
#             header_contents[tagId] =  value
#
#         elif(tagType == tyFloat8Array):
#             value = struct.unpack("<q", tagVal)[0]
#             #print('Float array with %d entries' % value / 8)
#
#         elif(tagType == tyAnsiString):
#             value = struct.unpack('<q', tagVal)[0]
#             string = ptureadstream.read(value).decode('latin1').strip('\0')
#             header_contents[tagId] =  string
#
#         elif(tagType == tyWideString):
#             value = struct.unpack('<q', tagVal)[0]
#             string = ptureadstream.read(value).decode('utf-16-le').strip('\0')
#             header_contents[tagId] =  string
#
#         elif(tagType == tyBinaryBlob):
#             value = struct.unpack("<q", tagVal)[0]
#             header_contents[tagId] =  value
#
#         elif(tagType == tyBitSet64):
#             value = struct.unpack('<q', tagVal)[0]
#             header_contents[tagId] =  value
#
#         elif(tagType == tyColor8):
#             value = struct.unpack('<q', tagVal)[0]
#             header_contents[tagId] =  "{0:#0{1}x}".format(value,18)
#
#         elif(tagType == tyBinaryBlob):
#             value = struct.unpack('<q', tagVal)[0]
#             header_contents[tagId] =  value
#
#         elif(tagType == tyTDateTime):
#             print('')
#
#         else:
#             continue
#             #print('Unknown header tag type. Ignored.')
#
#
#     headerend_bitoffset = ptureadstream.tell() # Needed to quickly jump to photon records instead of header
#
#     #print('Finished decoding header.')
#
#     # Copying header info into FLIMInfo dict
#
#     try:
#         FLIMInfo = {
#             'Filename' : header_contents['$Filename'],
#             'Comment': header_contents['$Comment'],
#             'RecordType' : header_contents['TTResultFormat_TTTRRecType'],
#             'BitsPerRecord' : header_contents['TTResultFormat_BitsPerRecord'],
#             'PixelResolution' : header_contents['$ReqHdr_SpatialResolution'],
#             'PixelsX' : header_contents['ImgHdr_PixX'],
#             'PixelsY' : header_contents['ImgHdr_PixY'],
#             'GlobalResolution' : header_contents['MeasDesc_GlobalResolution'],
#             'BaseResolution' : header_contents['HW_BaseResolution'],
#             'Resolution' : header_contents['MeasDesc_Resolution'],
#             'BinningFactor' : header_contents['MeasDesc_BinningFactor'],
#             'SyncRate' : header_contents['TTResult_SyncRate'],
#             'NumberOfRecords': header_contents['TTResult_NumberOfRecords'],
#             'LineStart': header_contents['ImgHdr_LineStart'],
#             'LineStop': header_contents['ImgHdr_LineStop']
#         }
#     except:
#         FLIMInfo = {
#             #'Filename' : header_contents['$Filename'],
#             #'Comment': header_contents['$Comment'],
#             'RecordType' : header_contents['TTResultFormat_TTTRRecType'],
#             'BitsPerRecord' : header_contents['TTResultFormat_BitsPerRecord'],
#             #'PixelResolution' : header_contents['$ReqHdr_SpatialResolution'],
#             'PixelsX' : header_contents['ImgHdr_PixX'],
#             'PixelsY' : header_contents['ImgHdr_PixY'],
#             'GlobalResolution' : header_contents['MeasDesc_GlobalResolution'],
#             'BaseResolution' : header_contents['HW_BaseResolution'],
#             'Resolution' : header_contents['MeasDesc_Resolution'],
#             'BinningFactor' : header_contents['MeasDesc_BinningFactor'],
#             'SyncRate' : header_contents['TTResult_SyncRate'],
#             'NumberOfRecords': header_contents['TTResult_NumberOfRecords'],
#             'LineStart': header_contents['ImgHdr_LineStart'],
#             'LineStop': header_contents['ImgHdr_LineStop']
#         }
#
#
#
#     #print(FLIMInfo['LineStart'], FLIMInfo['LineStop'])
#     # Closing read stream
#     ptureadstream.close()
#
#
#     # Reading photon records from ptu file, reopening read stream at headerend_bitoffset
#     ## Initializing record array with pre-defined data types and length (read from header -> NumberOfRecords)
#     recordBitType = np.dtype([('record', np.uint32), ('marker', np.uint8),
#                                   ('nanotime', np.float64), ('macrotime', np.float64)])
#     recordarray = np.zeros(
#             shape=FLIMInfo['NumberOfRecords'] - 1, dtype=recordBitType)
#
#     ## Getting macro and nano time conversion factors from FLIMInfo
#     macroMultFactor = FLIMInfo['GlobalResolution']
#     nanoMultFactor = FLIMInfo['Resolution'] * 1e9
#
#     ## Dumping records into recordarray
#     with open(path, 'rb') as file:
#         file.seek(headerend_bitoffset)
#         recordarray[:]['record'] = np.fromfile(file, dtype=np.uint32)
#         file.close()
#
#     ## Recover marker signals and nano times by bitwise operations on recordarray['record']
#     recordarray[:]['marker'] = (np.right_shift(recordarray[:]['record'], 25) & 127)
#     recordarray[:]['nanotime'] = ((np.right_shift(recordarray[:]['record'], 10) & 32767) * nanoMultFactor).astype(np.float64)
#
#     # Recover macro times using treat_overflows()
#     recordarray = treat_overflows(recordarray, macroMultFactor)
#
#     header_contents = FLIMInfo
#     header_contents['NumberOfLines'] = count_lines(recordarray)
#     header_contents['NumberOfFrames'] = int(header_contents['NumberOfLines'] / header_contents['PixelsX'])
#
#     #macrotimes = np.array(recordarray['macrotime'], dtype = np.float32)
#     #nanotimes = np.array(recordarray['nanotime'], dtype = np.float32)
#     #markers = np.array(recordarray['marker'], dtype = np.uint8)
#
#
#
#     return(recordarray, header_contents)


def read_ptu_file(path:str):

    # Opening ptu file in binary reading mode
    ptu_file = open(path, 'rb')

    # Check if file is valid
    file_magic = ptu_file.read(8).decode('utf-8').strip('\0')
    file_version = ptu_file.read(8).decode('utf-8').strip('\0')

    if file_magic != 'PQTTTR':
        ptu_file.close()
        raise IOError('Provided file is not a .ptu!')

    header_offset, header_contents, FLIM_Info = read_ptu_header(ptu_file)
    assert FLIM_Info['RecordType'] == rtHydraHarp2T3, 'Not a HydraHarpT3 V2 record type!'

    recordarray = read_ptu_photons(
        file = ptu_file,
        number_of_records = FLIM_Info['NumberOfRecords'],
        global_resolution = FLIM_Info['GlobalResolution'],
        base_resolution = FLIM_Info['BaseResolution']
    )

    return(recordarray, header_contents, FLIM_Info)


def read_ptu_header(file: object):

    # Tag that indicates end of header section in file
    header_end_tag = 'Header_End'
    reached_header_end = False

    # tuple that stores decoded information from header section
    header_contents = {}

    while reached_header_end is not True:
        header_piece = file.read(48)
        tag_id = header_piece[0:32].decode('latin1').strip('\0') # Necessary for non-US computer systems (If I remember correcly..., otherwise utf-8 encoding)
        tag_index = struct.unpack('<i', header_piece[32:36])[0]
        tag_type = struct.unpack('<i', header_piece[36:40])[0]
        tag_value = header_piece[40:48]

        # Looking for header end tag
        if(tag_id == header_end_tag):
            reached_header_end = True
            file.read(4) # Offset required so that photon records (see second part) are 'in frame'!
            break

        if(tag_type == tyEmpty8):
            header_contents['Empty'] =  'Empty'

        elif(tag_type == tyBool8):
            value = struct.unpack('<q', tag_value)[0]
            header_contents[tag_id] =  value

        elif(tag_type == tyInt8):
            value = struct.unpack('<q', tag_value)[0]
            header_contents[tag_id] =  value

        elif(tag_type == tyFloat8):
            value = struct.unpack('<d', tag_value)[0]
            header_contents[tag_id] =  value

        elif(tag_type == tyFloat8Array):
            value = struct.unpack("<q", tag_value)[0]
            #print('Float array with %d entries' % value / 8)

        elif(tag_type == tyAnsiString):
            value = struct.unpack('<q', tag_value)[0]
            string = file.read(value).decode('latin1').strip('\0')
            header_contents[tag_id] =  string

        elif(tag_type == tyWideString):
            value = struct.unpack('<q', tag_value)[0]
            string = file.read(value).decode('utf-16-le').strip('\0')
            header_contents[tag_id] =  string

        elif(tag_type == tyBinaryBlob):
            value = struct.unpack("<q", tag_value)[0]
            header_contents[tag_id] =  value

        elif(tag_type == tyBitSet64):
            value = struct.unpack('<q', tag_value)[0]
            header_contents[tag_id] =  value

        elif(tag_type == tyColor8):
            value = struct.unpack('<q', tag_value)[0]
            header_contents[tag_id] =  "{0:#0{1}x}".format(value,18)

        elif(tag_type == tyBinaryBlob):
            value = struct.unpack('<q', tag_value)[0]
            header_contents[tag_id] =  value

        elif(tag_type == tyTDateTime):
            print('')

        else:
            continue
            #print('Unknown header tag type. Ignored.')

    # Getting offset of header_end tag
    header_end_offset = file.tell()

    # Sorting important infos in tuple for quicker access
    FLIM_Info = {
        'RecordType' : header_contents['TTResultFormat_TTTRRecType'],
        'BitsPerRecord' : header_contents['TTResultFormat_BitsPerRecord'],
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

    return(header_end_offset, header_contents, FLIM_Info)

def read_ptu_photons(
    file: object,
    number_of_records: int,
    global_resolution: float,
    base_resolution: float
    ):
    # Reading photon records from ptu file, reopening read stream at headerend_bitoffset
    ## Initializing record array with pre-defined data types and length (read from header -> NumberOfRecords)
    record_bit_type = np.dtype([('record', np.uint32), ('marker', np.uint8),
                                  ('nanotime', np.float64), ('macrotime', np.float64)])
    recordarray = np.zeros(
        shape = number_of_records - 1,
        dtype = record_bit_type
    )

    # Getting 32 bit photon records from ptu file
    try:
        recordarray[:]['record'] = np.fromfile(file, dtype = np.uint32)
    except:
        raise IOError('Could not read photon records from .ptu file.')
    finally:
        file.close()

    # Getting markers, macrotime andnanotimes by bitwise operations
    ## markers are the first 7 bits in 32 bit intergers: 1 - special bit, 2 to 7 - channel
    recordarray[:]['marker'] = (
        np.right_shift(recordarray[:]['record'], 25) & (2**7 - 1)
    )

    ## nanotimes are in the following 15 bits
    recordarray[:]['nanotime'] = (
        np.right_shift(recordarray[:]['record'], 10) & (2**15 - 1)
    )

    ## macrotimes need to be corrected for macrotime clock overflows
    ## accelerated using numba
    recordarray[:]['macrotime'] = treat_overflows(
        recordarray,
        macrotime_factor = global_resolution,
        overflow_period = 1024
    )

    return(recordarray)


@jit(nopython = True)
def treat_overflows(recordarray: np.array, macrotime_factor: float, overflow_period: int):
    '''
    Function treat_overflows(
    recordarray: 4 x numRec NumPy array holding raw 32 bit photon records in ['record']
    macrotimefactor: multiplication factor for mactotime clock to recover real experiment macrotime
    )
    Output is recordarray, but with populated ['macrotime'] row

    Takes whole record array and recovers real macrotime from raw photon TTTR data by adding
    number of macrotime clock overflows. See PicoQuant PTU documentary for further details and explanation.
    '''

    overflow_correction = 0

    for record in recordarray:
        # Overflow indicated by all marker bits set
        if record['marker'] == 127:
            # Getting number of overflows since experiment start
            # is written in macrotime field in case of overflow
            overflow_correction += overflow_period * np.bitwise_and(record['record'], (2**10 - 1))

        # Get macrotime from macrotime field and correcting overflow
        record['macrotime'] = (
            overflow_correction + np.bitwise_and(record['record'], (2**10 - 1))
        )

    return(recordarray['macrotime'])



@jit(nopython = False, cache = True)
def sinus_correction(correction_factor:float, number_of_pixels: int, pixel_mult_factor: int = 10):
    """ Calculates look-up table for lines from sinusodial scanning.
        The linear pixel time is then converted to the corresponding
        pixel in an image where sinusodial scanning has been corrected.

    Args:
        correction_factor (float): [description]
        number_of_pixels (int): [description]
        pixel_mult_factor (int): Excess of of pixels in look-up table. Defaults to 10.
    """
    corrected_bins = np.linspace(-(correction_factor), (correction_factor), (pixel_mult_factor * number_of_pixels))
    np.sin(corrected_bins, corrected_bins)
    np.add(corrected_bins, np.max(corrected_bins), corrected_bins)
    np.multiply(corrected_bins, 1/np.max(corrected_bins), corrected_bins)
    np.multiply(corrected_bins, (number_of_pixels - 1), corrected_bins)

    return(corrected_bins, pixel_mult_factor)



#@jit(nopython=True, cache=True)
def build_flim_array(
    recordarray: np.ndarray,
    channel: int,
    lines_in_file: int,
    pixels_x: int, pixels_y: int,
    global_resolution: float, time_resolution: float,
    spatial_binning: float, decay_binning: float,
    sinusodial_correction: float = 0.0001,
    line_start_marker: int = 1, line_stop_marker: int = 2):
    """Reconstructs FLIM array (x-y-decay) from PicoQuant TTTR data
        generated by read_ptu_data().

    Args:
        recordarray (np.ndarray [records, macrotime, nanotime, markers]): [description]
        channel (int): Indicates photon channel that is used for image reconstruction.
        lines_in_file (int): Y pixels (lines) in the TTTR data.
        pixels_x (int): pixels of the image in x
        pixels_y (int): Pixels of the image in y
        global_resolution (float): Time between laser pulses (a.k.a. laser repetition rate)
        time_resolution (float): Base TCSPC resolution of nanotime (typically 16 ps)
        spatial_binning (float): Use > 1 to reduce the number of x-y-pixels in the resulting image
        decay_binning (float): Use > 1 to reduce number of bins of fluorescence decay
        sinusodial_correction (float, optional): Amount of sinusodial correction for image reconstruction. Defaults to 0.0001.
        line_start_marker / line_stop_marker (int, optional): Sets values for line start and line stop events for image reconstuction.
    """
    # Setting up counters
    event_counter = 0           # Used to loop through records in recordarray
    line_counter = 0            # keeps track of current line in image (y)
    frame_counter = 0           # keeps track of current line (x)

    # Setting up reconstruction constants
    frames_in_file = math.floor(lines_in_file)
    decay_bins =math.ceil(
            (global_resolution / time_resolution)/(2**decay_binning))
    global_resolution *= 10E8   # Time between pulses in ns
    time_resolution *= 10E9     # TCSPC time resolution in ns
    binning_factor = 2**spatial_binning
    # Getting line markers. Cave: The marker array consists of 7 bits,
    # thus including the special bit.
    # Because the special bit is set in case of a system event, all system
    # markers will have an 'offset' of 64, e.g. (1 - 000001) for line start
    marker_line_start = 64 + line_start_marker
    marker_line_stop = 64 + line_stop_marker

    # Setting up temporary variables for reconstruction
    line_start = None           # macrotime of current line start marker
    line_stop = None            # macrotime of the current line stop marker
    pixel_time = None           # macrotime per pixel in the current line
    average_line_time = None    # average macrotime per line, used for exceptions
    line_active = False         # Set to true after line start marker is found
    last_line = False           # Set true when last line in frame is reached
    photon_list_macro = [np.float64(x) for x in range(0)]
    photon_list_nano =  [np.float64(x) for x in range(0)]
    tmp_marker = None
    tmp_macro = None
    tmp_nano = None
    time_difference = None
    number_of_pixels_x = int(pixels_x / binning_factor)
    number_of_pixels_y = int(pixels_y / binning_factor)
    pixel_id_x = 0           # Current pixel in x (frame)
    pixel_id_y = 0           # Current pixel in y (line)


    # Pre-initializing FLIM array for data to be sorted into
    flim_array = np.zeros(
        (number_of_pixels_x, number_of_pixels_y, decay_bins),
        dtype = np.uint16)
    image_array = np.zeros(
        (number_of_pixels_x, number_of_pixels_y),
        dtype = np.uint16
    )

    '''
    Calculating sinusodial scan correction lookup table
    using sinus_correction() function:
    sinus_correction() takes number of pixels and desired
    correction factor which specifies what percentage of
    the sinus curve is used for mapping of pixels and thus
    correction of the distorted image.
    An excess of corrected bins is produced and handeled
    as float(!) because some pixels will be rounded to
    other values and to not map to an actual pixel on a
    particular line.
    '''
    corrected_bins, correction_mult_factor = sinus_correction(
        sinusodial_correction,
        number_of_pixels_y,
        pixel_mult_factor = 10
    )


    '''
    Main loop for image reconstruction
    ---
    Photon records in recordarray are now looped through
    and each marker in the recordarray is checked for
    marker events (line start and stop).
    When a line start is encountered, all events and
    nanotimes from start to line end are collected in
    tmp_events and tmp_nano in the order that they appeared
    in the array.
    The time difference between line start and stop
    macrotimes is used to sort the events into the
    corresponding pixel in the image and the TCSPC bin.
    After each line, pixel counters are iterated and it
    is checked if they exceed the constants set in the
    beginning. If the line counter exceeds the number of
    pixels in the x direction, a new frame is started and
    thus all pixel counters are reset.
    Each
    '''

    while last_line is False:
        tmp_marker = recordarray['marker'][event_counter]
        # Check if marker is a line start event
        if tmp_marker == marker_line_start:
            line_active = True
            line_start = recordarray['macrotime'][event_counter]
            event_counter += 1
            continue

        while line_active:
            tmp_marker = recordarray['marker'][event_counter]
            tmp_macro = recordarray['macrotime'][event_counter]
            tmp_nano = recordarray['nanotime'][event_counter]

            if tmp_marker == channel:
                # Add current photon to tmp_event and tmp_nano
                # of it comes from user-chosen photodetector channel
                photon_list_macro.append(tmp_macro)
                photon_list_nano.append(tmp_nano)

            elif tmp_marker == marker_line_stop:
                # Check for line stop marker
                line_active = False
                line_stop = tmp_macro

                # Get time per pixel from line stop and line start macrotimes
                pixel_time = (line_stop - line_start) / number_of_pixels_y
                # Sort photons from photon lists into flim_array and image_array
                for i in range(0, len(photon_list_macro)):
                    time_difference = photon_list_macro[i] - line_start
                    bin_id = int(math.floor( # Decay bin
                        (photon_list_nano[i] / global_resolution) * decay_bins - 1
                    ))
                    print(bin_id)
                    pixel_id_y = int(round(corrected_bins[int(time_difference)]))
                    # Check if photon is out-of-bounds of image
                    if pixel_id_y < 0:
                        pixel_id_y = 0
                    elif pixel_id_y > (number_of_pixels_y - 1):
                        pixel_id_y = (number_of_pixels_y - 1)
                    # Add photon to corresponding position in flim and image array
                    flim_array[int(math.floor(pixel_id_x))][pixel_id_y][bin_id] += 1
                    image_array[int(math.floor(pixel_id_x))][pixel_id_y] += 1

                # Incrementing image counter variables
                ## Incrementing pixel_id_x with fraction of binning factor
                ## in assignment to the image pixel this value is floored
                ## Otherwise artifical, user-chosen binning would clash
                ## with the actual number of line marker in the TTTR.
                pixel_id_x += (1 / binning_factor)
                line_counter += 1

                # Clearing tmp photon lists
                photon_list_macro = [np.float64(x) for x in range(0)]
                photon_list_nano = [np.float64(x) for x in range(0)]

            event_counter += 1

        event_counter += 1

        # Check if line exceeds image x dimension
        if line_counter > (number_of_pixels_x - 1):
            frame_counter += 1
            pixel_id_x = 0
            continue

        # Check of global exit: last frame or no more events
        if frame_counter >= frames_in_file or event_counter >= len(recordarray['marker']):
            last_line = True
            continue

    return(flim_array, image_array)


@jit(nopython=True, cache=True)
def build_frame_array(
    recordarray: np.ndarray,
    channel: int,
    lines_in_file: int,
    pixels_x: int, pixels_y: int,
    spatial_binning: float,
    sinusodial_correction: float = 0.0001):
    """Same as build_flim_array but puts each found frame
        in image array, i.e. each scanned frame comes after the other
        without the decay being added.

    Args:
        recordarray (np.ndarray [records, macrotime, nanotime, markers]): [description]
        channel (int): Indicates photon channel that is used for image reconstruction.
        lines_in_file (int): Y pixels (lines) in the TTTR data.
        pixels_x (int): pixels of the image in x
        pixels_y (int): Pixels of the image in y
        spatial_binning (float): Use > 1 to reduce the number of x-y-pixels in the resulting image
        sinusodial_correction (float, optional): Amount of sinusodial correction for image reconstruction. Defaults to 0.0001.


    """
    # Setting up counters
    event_counter = 0           # Used to loop through records in recordarray
    line_counter = 0            # keeps track of current line in image (y)
    frame_counter = 0           # keeps track of current line (x)

    # Setting up reconstruction constants
    frames_in_file = math.floor(lines_in_file)
    binning_factor = 2**spatial_binning
    marker_line_start = 65
    marker_line_stop = 66

    # Setting up temporary variables for reconstruction
    line_start = None           # macrotime of current line start marker
    line_stop = None            # macrotime of the current line stop marker
    pixel_time = None           # macrotime per pixel in the current line
    average_line_time = None    # average macrotime per line, used for exceptions
    line_active = False         # Set to true after line start marker is found
    last_line = False           # Set true when last line in frame is reached
    photon_list_macro = [np.float64(x) for x in range(0)]
    tmp_marker = None
    tmp_macro = None
    time_difference = None
    number_of_pixels_x = int(pixels_x / binning_factor)
    number_of_pixels_y = int(pixels_y / binning_factor)
    pixel_id_x = None           # Current pixel in x (frame)
    pixel_id_y = None           # Current pixel in y (line)


    # Pre-initializing image array for data to be sorted into
    image_array = np.zeros(
        (number_of_pixels_x, number_of_pixels_y, frames_in_file),
        dtype = np.uint16
    )

    '''
    Calculating sinusodial scan correction lookup table
    using sinus_correction() function:
    sinus_correction() takes number of pixels and desired
    correction factor which specifies what percentage of
    the sinus curve is used for mapping of pixels and thus
    correction of the distorted image.
    An excess of corrected bins is produced and handeled
    as float(!) because some pixels will be rounded to
    other values and to not map to an actual pixel on a
    particular line.
    '''
    corrected_bins, correction_mult_factor = sinus_correction(
        sinusodial_correction,
        number_of_pixels_y,
        pixel_mult_factor = 10
    )


    '''
    Main loop for image reconstruction
    ---
    Photon records in recordarray are now looped through
    and each marker in the recordarray is checked for
    marker events (line start and stop).
    When a line start is encountered, all events and
    nanotimes from start to line end are collected in
    tmp_events and tmp_nano in the order that they appeared
    in the array.
    The time difference between line start and stop
    macrotimes is used to sort the events into the
    corresponding pixel in the image and the TCSPC bin.
    After each line, pixel counters are iterated and it
    is checked if they exceed the constants set in the
    beginning. If the line counter exceeds the number of
    pixels in the x direction, a new frame is started and
    thus all pixel counters are reset.
    Each
    '''

    while not last_line:
        tmp_marker = recordarray['marker'][event_counter]

        # Check if marker is a line start event
        if tmp_marker == marker_line_start:
            line_active = True
            line_start = recordarray['macrotime'][event_counter]
            event_counter += 1
            continue

        while line_active:
            tmp_marker = recordarray['marker'][event_counter]
            tmp_macro = recordarray['macrotime'][event_counter]

            if tmp_marker == channel:
                # Add current photon to tmp_event and tmp_nano
                # of it comes from user-chosen photodetector channel
                photon_list_macro.append(tmp_macro)
            elif tmp_marker == marker_line_stop:
                # Check for line stop marker
                line_active = False
                line_stop = tmp_macro

                # Get time per pixel from line stop and line start macrotimes
                pixel_time = (line_stop - line_start) / number_of_pixels_y

                # Sort photons from photon lists into flim_array and image_array
                for i in range(0, len(photon_list_macro)):
                    time_difference = round(
                        correction_mult_factor * (photon_list_macro[i] - line_start) / pixel_time
                    )

                    pixel_id_y = int(round(corrected_bins[int(time_difference)]))

                    # Check if photon is out-of-bounds of image
                    if pixel_id_y < 0:
                        pixel_id_y = 0
                    elif pixel_id_y > (number_of_pixels_y - 1):
                        pixel_id_y = (number_of_pixels_y - 1)

                    # Add photon to corresponding position in flim and image array
                    image_array[math.floor(pixel_id_x)][pixel_id_y][frame_counter] += 1

                    # Incrementing image counter variables
                    ## Incrementing pixel_id_x with fraction of binning factor
                    ## in assignment to the image pixel this value is floored
                    ## Otherwise artifical, user-chosen binning would clash
                    ## with the actual number of line marker in the TTTR.
                    pixel_id_x += (1 / binning_factor)
                    line_counter += 1

                    # Clearing tmp photon lists
                    photon_list_macro = [np.float64(x) for x in range(0)]

                event_counter += 1

            # Check if line exceeds image x dimension
            if line_counter > (number_of_pixels_x - 1):
                frame_counter += 1
                pixel_id_x = 0

            # Check of global exit: last frame or no more events
            if frame_counter >= frames_in_file or event_counter >= len(recordarray['marker']):
                last_line = True

            event_counter += 1

        return(image_array)





def make_time_axis(global_resolution, resolution, number_of_bins = 0):
    t_end = global_resolution * 1E12
    dt = resolution * 1E12

    if(number_of_bins == 0):
        number_of_bins = math.ceil(t_end / dt)

    t_axis = np.linspace(0, t_end, number_of_bins)

    return(t_axis)


def load_flim_data(
	path:str,
	channel: int = 0,
	spatial_binning: float = 0,
	decay_binning: float = 0,
	sinusodial_correction: float = 0.0001):
    '''
    Function wrapper for read_ptu_data and build_flim_array.
    Returns the 3D FLIM array and the intensity image of the ptu file provided with path (str).
    '''
    recordarray, header_contents, FLIM_Info = read_ptu_file(path)
    FLIM_Info['LinesInFile'] = count_lines(recordarray)

    flim_array, intensity_image = build_flim_array(
      recordarray = recordarray,
      channel = channel,
      lines_in_file = FLIM_Info['LinesInFile'],
      pixels_x = FLIM_Info['PixelsX'],
      pixels_y = FLIM_Info['PixelsY'],
      global_resolution = FLIM_Info['GlobalResolution'],
      time_resolution = FLIM_Info['Resolution'],
      spatial_binning = spatial_binning,
      decay_binning = decay_binning,
      sinusodial_correction = sinusodial_correction
    )

    time_axis = make_time_axis(
        FLIM_Info['GlobalResolution'],
        FLIM_Info['Resolution'],
        number_of_bins = flim_array.shape[2]
    )

    return(flim_array, intensity_image, time_axis)
