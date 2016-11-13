#!d:\\python27 python2.7
# -*- coding: cp936 -*-

import powermesh_rscodec
from pvm_util import *


BIT_DLL_SEND_PROP_EDP = 0x10
BIT_DLL_SEND_PROP_SCAN = 0x08

EXP_EDP_EBC_NBF = 0x00
EXP_EDP_EBC = 0x40


def encode_xmode(xmode, scan):
    """
        4-bit Xmt Mode Code Table:
        0x0:CH0+BPSK;0x1:CH1+BPSK;0x2:CH2+BPSK;0x3:CH3+BPSK
        0x4:CH0+DS15;0x5:CH1+DS15;0x6:CH2+DS15;0x7:CH3+DS15
        0x8:CH0+DS63;0x9:CH1+DS63;0xA:CH2+DS63;0xB:CH3+DS63
        (SCAN==0)
        0x0C:SALVO+BPSK;0x0D:SALVO+DS15;0x0E:SALVO+DS63;
        (SCAN==1)
        0x0C:SCAN+BPSK;0x0D:SCAN+DS15;0x0E:SCAN+DS63;
    * Input          : xmode, xmode must be either single channel or salvo mode if not scan enable;
    * Output         :
    * Return         : code
    """
    assert xmode & 0xF0 in (0x10, 0x20, 0x40, 0x80, 0xF0), "error xmode"
    assert xmode & 0x0F in (0x00, 0x01, 0x02), "error xmode"

    if scan:
        xcode = 0x0C + (xmode & 0x03)
    else:
        if xmode & 0xF0 == 0xF0:
            xcode = 0x0C + (xmode & 0x03)
        else:
            xcode = 0x03 if ((xmode >> 5) == 4) else (xmode >> 5)
            xcode += ((xmode & 0x0F) << 2)
    return xcode

class Powermesh():
    '''A powermesh frame object
    '''


    def __init__(self, interface):
        """establish a powermesh obj by a frame of rcv_loop phy data or nothing('', for generate a phy frame)
        Params:
            interface: CV object handle
        """
        self.interface = interface

        self.broad_id = 1
        pass

    def app_send(self):
        pass

    def dll_send(self, target_uid, lsdu, prop = 0, xmode = 0x80, rmode = 0x80, delay = 0):

        pass

    def phy_rcv_proc(self, ppdu):
        psdu = []
        return psdu

    def dll_rcv_proc(self, lpdu):
        lsdu = []
        return lsdu

    def nw_rcv_proc(self, npdu):
        pass

    def run_rcv_proc(self, ppdu):
        pass

    def ebc_broadcast(self, update_bid = True, xmode = 0x10, rmode = 0x10, scan = 1, mask = 0, window = 5):
        """
            broadcast
        """

        if update_bid:
            self.broad_id = (self.broad_id + 1) % 0x0F
            if self.broad_id == 0:
                self.broad_id = 1

        lsdu = [EXP_EDP_EBC | (encode_xmode(rmode, scan) << 2) | EXP_EDP_EBC_NBF, self.broad_id<<4 | window, mask]
        prop = BIT_DLL_SEND_PROP_EDP | (BIT_DLL_SEND_PROP_SCAN if scan else 0)

        self.interface.dll_send([0,0,0,0,0,0], lsdu, prop, xmode, rmode, delay = 0.02)

