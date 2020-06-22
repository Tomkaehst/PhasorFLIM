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
    def __init__(self, file_path: str, channel: int, spatial_binning: int, temporal_binning: int, fast_load: bool = True):
        """[summary]

        Arguments:
            file_path {str} -- [description]
            spatial_binning {int} -- [description]
            temporal_binning {int} -- [description]
            fast_load {bool} -- Fast loading of ptu file and generation of FLIM array, if true.
        """

        self.file_path = file_path
        self.spatial_binning = spatial_binning
        self.temporal_binning = temporal_binning

        # Defining data types for the raw record array where ptu data stream is written in to
        self.record_array_datatypes = np.dtype([('record', np.uint32), ('marker', np.uint8),
                                                ('nanotime', np.float64), ('macrotime', np.float64)])

        self.FLIMInfo = None  # Quick access FLIM image infos
        self.header_contents = None  # Whole file header
        # Bit offset of file in file_path, where TTTR records start
        self.headerBitOffset = None


        # Reading header; do this automatically when flimdata instance is created; no great time pennalty
        self.readPTUHeader(self.file_path)

        if (fast_load is True):
            self.readPTUHeader(self.file_path)
            # Loading photon data into recordarray
            self.recordarray = self.readPhotonData(
                self.file_path, self.headerBitOffset, self.FLIMInfo['NumberOfRecords']
            )
            # Generating nano tim(se axis
            self.time_axis = self.generate_nanotime_axis()
            # Getting list of channels from the data
            self.FLIMInfo['availableChannels'] = self.checkChannelAvailability(
                self.recordarray)

            if (channel is None):
                self.selected_channel = self.FLIMInfo['availableChannels'][0]
            else:
                self.selected_channel = channel

            # Counting line events, requires for image reconstruction
            self.FLIMInfo['Lines_in_file'] = self.countLines(self.recordarray)

            # Reconstruct FLIM array for fitting
            self.flimarray, self.intensity_image = self.reconstruct_flim_array(
                self.recordarray,
                channel=self.selected_channel,
                lines_in_file=self.FLIMInfo['Lines_in_file'],
                pixels_x=self.FLIMInfo['PixelsX'],
                pixels_y=self.FLIMInfo['PixelsY'],
                global_resolution=self.FLIMInfo['GlobalResolution'],
                time_resolution=self.FLIMInfo['Resolution'],
                spatial_binning=self.spatial_binning,
                temporal_binning=self.temporal_binning
            )

            # Generating overall decay histograms from available channels
            self.overall_decays = self.overall_decay()

            self.selected_decay = None


    def readPTUHeader(self, file_path):
        """[summary]

        Arguments:
            file_path {[type]} -- [description]
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
        filereadstream = open(self.file_path, 'rb')

        # Checking first 8 bytes for correct file magic
        filemagic = filereadstream.read(8).decode('utf8').strip('\0')
        if(filemagic != 'PQTTTR'):
            print('%s is not a valid PTU file. Aborting.' % self.file_path)
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
        # - MeasDesc_Resolution: TCSPC resolution, also obtained by BaseResolution * binning_factor
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

    def readPhotonData(self, file_path: str, bitoffset: int, numRecords: int):
        """[summary]

        Arguments:
            file_path {string} -- [description]
            bitoffset {int} -- [description]
            numRecords {int} -- [description]
        """

        # Initializing recordarray
        recordarray = np.zeros(shape=numRecords - 1,
                               dtype=self.record_array_datatypes)

        # Reading data from file into recordarray
        with open(file_path, 'rb') as file:
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
        nano_mult_factor = self.FLIMInfo['Resolution'] * 1e9
        macro_mult_factor = self.FLIMInfo['GlobalResolution']

        recordarray['marker'] = (np.right_shift(
            recordarray[:]['record'], 25) & 127)
        recordarray[:]['nanotime'] = ((np.right_shift(
            recordarray[:]['record'], 10) & 32767) * nano_mult_factor).astype(np.float32)

        recordarray = self.treat_overflows(recordarray, macro_mult_factor)

        return(recordarray)

    '''
    In order to use Numba in a class method, the method needs to be defined as static.
    This means, that it has no direct access to self and all arguments need to be explicitly passed
    to that function.
    '''
    @staticmethod
    @jit(nopython=True, cache=True)
    def treat_overflows(recordarray: np.ndarray, macrotimefactor: float):
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

        num_line_start = np.sum(recordarray['marker'] == 65)
        num_line_stop = np.sum(recordarray['marker'] == 66)

        if(num_line_start != num_line_stop):
            print(
                'Number of line start and line stop markers does not match. File may be corrupted.'
            )

        return(num_line_start, num_line_stop)

    # @jit(nopython=True, cache=True)
    def checkChannelAvailability(self, recordarray: np.ndarray):
        """[summary]

        Arguments:
            recordarray {np.ndarray} -- [description]
        """

        # Initialized as numba.typed.List, because Python lists will be deprecated in future Numba versions
        channel_list = List()

        if(np.any(recordarray['marker'] == 0)):
            channel_list.append(0)
        if(np.any(recordarray['marker'] == 1)):
            channel_list.append(1)
        if(np.any(recordarray['marker'] == 2)):
            channel_list.append(2)
        if(np.any(recordarray['marker'] == 3)):
            channel_list.append(3)

        return(channel_list)

    def generate_nanotime_axis(self):
        t_end = self.FLIMInfo['GlobalResolution'] * \
            1E12  # Converting to picoseconds
        dt = self.FLIMInfo['Resolution'] * 1E12
        number_of_bins = math.ceil((t_end / dt) / 2**self.temporal_binning)
        time_axis = np.linspace(0, t_end, number_of_bins)
        return(time_axis)

    def overall_decay(self):
        """[summary]

        Arguments:
            recordarray {np.array} -- [description]
            channel_list {List[int]} -- [description]
        """

        decay = np.sum(np.sum(self.flimarray, axis=1), axis=0)

        return(decay)

    def sum_up_selected_decay(self, start_x, stop_x, start_y, stop_y):
        decay = np.sum(
            np.sum(self.flimarray[start_x:stop_x, start_y:stop_y], axis=0), axis=0)
        self.selected_decay = decay

    @staticmethod
    @jit(nopython=True)
    def reconstruct_flim_array(recordarray: np.ndarray,
                               channel: int,
                               lines_in_file: int,
                               pixels_x: int,
                               pixels_y: int,
                               global_resolution: float,
                               time_resolution: float,
                               spatial_binning: int,
                               temporal_binning: int):
        '''
        buildFLIMArray(
        - recordarray: 4 x numRec NumPy array, holds raw photon data and system events
        - channel: int; which channel to reconstruct the flimarray from
        - pixels_x: original image dimension in X, stored in FLIMInfo
        - pixels_y: original image dimension in Y, stored in FLIMInfo
        - global_resolution: global measurment of nanotime, stored in FLIMInfo, in ns, 51 ns for 20 MHz laser pulse frequency
        - time_resolution: nanotime resolution of TCSPC device, in ps
        - spatial_binning: user-defined binning factor of image, calculated as 2**factor
        - temporal_binning: user-defined binning factor for fluorescence decay histogram
        )
        '''

        event_counter = 0  # Keeps track of photon / marker events while looping through data
        line_counter = 0  # Stores current scan line numbers
        frame_counter = 0  # Stores current frame number
        # How many frames are in the image; assume square format

        frames_in_file = int(lines_in_file[0] / pixels_x)
        # Number of TCSPC bins based on time between pulses and TCSPC time resolution
        decay_bins = math.ceil(
            (global_resolution / time_resolution)/(2**temporal_binning))
        global_resolution = global_resolution * 10E8  # time between pulses in ns
        time_resolution = time_resolution * 10E9  # TCSPC time resolution in ns

        binning_factor = 2**spatial_binning

        line_start = 0
        line_stop = 0
        pixel_time = 0  # Tmp variable for storing time/pixel when line start and stop macro times are determined; needed to assign photons to y pixels in a line

        # Set to True when last scan line was evaluated and frame_counter >= frames_in_file
        last_line = False
        # Set to True when line start marker is found (= 65), starts photon assignments to y-pixels in a line (x); set to False when line stop marker is found (=66)
        line_active = False

        # List storing photon macrotimes when line is active to determine y-pixel position of photon
        tmp_events = [np.float64(x) for x in range(0)]
        # List storing photon nanotimes to assign to 3D-FLIM array in x-y position
        tmp_nano = [np.float64(x) for x in range(0)]
        tmp_marker = 0  # Holds marker value for one loop iteration
        tmp_macro = 0  # Holds macrotime value for one loop iteration
        tmp_nanotime = 0  # Holds nanotime value for one loop iteration
        diff = 0  # Stores difference between photon macro time and line start to determine photon y-position
        # Count out-of-range photons (photons with macrotime below or above line time difference)
        #oorPhotons = 0

        nPixelX = int(pixels_x / binning_factor)
        nPixelY = int(pixels_y / binning_factor)

        pixel_id_x = 0  # Current x position in image
        pixel_id_y = 0  # Current y position in image

        flimarray = np.zeros((nPixelX, nPixelY, decay_bins), dtype=np.uint16)
        intensity_image = np.zeros((nPixelX, nPixelY), dtype=np.uint16)

        while(last_line == False):
            tmp_marker = recordarray['marker'][event_counter]

            if(tmp_marker == 65):  # Event is line start marker
                # Starting line evaluation (next while loop)
                line_active = True
                # Store line start time
                line_start = recordarray['macrotime'][event_counter]
                event_counter += 1
                continue  # Skip this loop iteration

            while(line_active == True):
                tmp_marker = recordarray['marker'][event_counter]
                tmp_macro = recordarray['macrotime'][event_counter]
                tmp_nanotime = recordarray['nanotime'][event_counter]

                if(tmp_marker == channel):
                    tmp_events.append(tmp_macro)
                    tmp_nano.append(tmp_nanotime)
                elif(tmp_marker == 66):
                    line_active = False
                    line_stop = tmp_macro
                    pixel_time = (line_stop - line_start) / (nPixelY)

                    # Build intensity image and FLIM array from photon macro times
                    for i in range(0, len(tmp_events)):
                        diff = tmp_events[i] - line_start
                        pixel_id_y = int(math.floor(diff / pixel_time))
                        bin_id = math.floor(
                            (tmp_nano[i]/global_resolution)*decay_bins) - 1

                        if(pixel_id_y < 0):
                            pixel_id_y = 0
                        elif(pixel_id_y > (nPixelY - 1)):
                            pixel_id_y = nPixelY - 1

                        intensity_image[math.floor(
                            pixel_id_x)][pixel_id_y] += 1
                        flimarray[math.floor(pixel_id_x)
                                  ][pixel_id_y][bin_id] += 1

                    pixel_id_x += 1/binning_factor
                    line_counter += 1
                    tmp_events = [np.float64(x) for x in range(0)]
                    tmp_nano = [np.float64(x) for x in range(0)]

                event_counter += 1

            if(line_counter > (pixels_x - 1)):
                frame_counter += 1
                pixel_id_x = 0
                line_counter = 0

            if(frame_counter >= frames_in_file):
                last_line = True

            event_counter += 1

        return(flimarray, intensity_image)
