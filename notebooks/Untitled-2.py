
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
    assert FLIM_Info['RecordType'] != rtHydraHarp2T3, 'Not a HydraHarpT3 V2 record type!'

    recordarray = read_ptu_photons(
        file = ptu_file,
        number_of_records = FLIM_Info['NumberOfRecords'],
        global_resolution = FLIM_Info['GlobalResolution']
        base_resolution = FLIM_Info['BaseResolution']
    )


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

    print(header_contents)

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
    bit_offset: int,
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
    recordarray[:]['macrotime'] = treat_overflows(recordarray, macrotime_factor, overflow_period = 1024)

    return(recordarray)


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
