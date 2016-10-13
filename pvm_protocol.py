#!d:\\python27 python2.7
# -*- coding: cp936 -*-

POWERMESH_INNER_DATA_TYPE = list
#test
def asc_hex_to_dec_list(asc_hex_str):
    assert (len(asc_hex_str) % 2 == 0), 'input length error: %s' % (asc_hex_str,)
    temp = [int(asc_hex_str[i:i+2],16) for i in xrange(len(asc_hex_str)) if i % 2 == 0]
    return POWERMESH_INNER_DATA_TYPE(temp)


def crc16(data):
    '''
    :param data: input dec list
    :return:dec list for calce
    '''
    assert(type(data)==POWERMESH_INNER_DATA_TYPE), 'input data must be a %s' % (POWERMESH_INNER_DATA_TYPE,)

    crc = 0xFFFF
    for newbyte in data:
        for j in xrange(8):
            crcbit = 1 if (crc & 0x8000) else 0
            databit = 1 if (newbyte & 0x80) else 0
            crc = (crc<<1) % 0x10000
            if(crcbit != databit):
                crc ^= 0x1021
            newbyte = (newbyte<<1) % 0x100
    crc ^= 0xFFFF

    return POWERMESH_INNER_DATA_TYPE([crc>>8, crc%256])

class PowerMesh():
    '''A powermesh frame object

    '''

    def __init__(self, phy_data='', encode='asc_hex'):
        '''establish a powermesh obj by a frame of receiving phy data or nothing('', for generate a phy frame)
        :param phy_data: received phy frame, usually consisted of asc hex string
        :param encode: format of phy_data, default 'asc_hex', other option: 'str', 'dec_list'
        :return:
        '''
        if phy_data != '' and encode == 'asc_hex':
            self.data = POWERMESH_INNER_DATA_TYPE(asc_hex_to_dec_list(phy_data))

        pass;

    def parse(self):
        pass



if '__main__'==__name__:
    print list(crc16(POWERMESH_INNER_DATA_TYPE([173,   101,    94,   252,     9,   226,   233,   203,    25,    67,    85,   174,    34,   184,    27])))

    print asc_hex_to_dec_list('12345678')
