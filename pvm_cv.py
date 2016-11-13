#!d:\\python27 python2.7
# -*- coding: cp936 -*-
# author: Lv Haifeng
# ver: 1.0
# 2016-10-18

from pvm_interface import CV
from pvm_util import *

class CV(object):
    def __init__(self, port, baudrate = 115200):
        self.interface = CV(port, baudrate)

    def close(self):
        self.interface.close()

    def diag(self, target_uid, xmode = 0x10, rmode = 0x10, scan = 0x01):
        """
            diag a module by uid formated as an ascii hex str, e.g. '5e1d0a05ff'
        Params:
            target_uid: an 12-byte asc hex str
            xmode:
                0x10:   CH0(131.58kHz), bpsk(5.4825kbps);
                0x20:   CH1(263.16kHz), bpsk;
                0x40:   CH2(312.5kHz), bpsk;
                0x80:   CH3(416.67kHz), bpsk;
                0xf0:   SALVO(CH0+CH1+CH2+CH3), bpsk;
                0x11:   CH0, ds15(365.4971bps);
                0x21:   CH1, ds15;
                0x41:   CH2, ds15;
                0x81:   CH3, ds15;
                0xf1:   SALVO(CH0+CH1+CH2+CH3), ds15;
                0x12:   CH0, ds63(87.0231bps);
                0x22:   CH1, ds63;
                0x42:   CH2, ds63;
                0x82:   CH3, ds63;
                0xf2:   SALVO(CH0+CH1+CH2+CH3), ds63;
            rmode:
                same as xmode
            scan:
                ch scan mode
        """

        frame = '000012' + target_uid + dec_array_to_asc_hex_str([xmode, rmode, scan])
        frame = asc_hex_str_to_dec_array(frame)
        frame += crc16(frame)
        ret = self.interface.single_response_transaction(frame)
        print ret

if __name__ == '__main__':
    try:
        cv = CV('com3')
        cv.diag('ffffffffffff')
    finally:
        cv.close()
    print ('END')