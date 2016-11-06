#!d:\\python27 python2.7
# -*- coding: cp936 -*-

POWERMESH_INNER_DATA_TYPE = list                  # in release version, inner data type should be bytearray
PRINT_DEBUG_INFO = True

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

