#!d:\\python27 python2.7
# -*- coding: cp936 -*-

POWERMESH_INNER_DATA_TYPE = list                  # in release version, inner data type should be bytearray
PRINT_DEBUG_INFO = True

class PvmFatalException(Exception):
    """ The exceptions when raised the whole process should quit
    """
    pass





def asc_hex_str_to_dec_array(asc_hex_str):
    assert (len(asc_hex_str) % 2 == 0), 'input length error: %s' % (asc_hex_str,)
    temp = [int(asc_hex_str[i:i+2],16) for i in xrange(len(asc_hex_str)) if i % 2 == 0]
    return POWERMESH_INNER_DATA_TYPE(temp)


def dec_array_to_asc_hex_str(dec_list, seperator = ''):
    temp = ['%02X' % n for n in dec_list]
    return seperator.join(temp)

def debug_output(s):
    if PRINT_DEBUG_INFO:
        print(s)


def crc16(data):
    """
    Params:
        data: input dec list
    Return:
        dec list for calce
    """
    assert(type(data)==POWERMESH_INNER_DATA_TYPE), 'input data must be a %s' % (POWERMESH_INNER_DATA_TYPE,)

    crc = 0xFFFF
    for newbyte in data:
        for j in xrange(8):
            crcbit = 1 if (crc & 0x8000) else 0
            databit = 1 if (newbyte & 0x80) else 0
            crc = (crc<<1) % 0x10000
            if crcbit != databit:
                crc ^= 0x1021
            newbyte = (newbyte<<1) % 0x100
    crc ^= 0xFFFF

    return POWERMESH_INNER_DATA_TYPE([crc>>8, crc%256])