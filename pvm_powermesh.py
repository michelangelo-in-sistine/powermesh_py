#!d:\\python27 python2.7
# -*- coding: cp936 -*-

import powermesh_rscodec
from pvm_util import *
from powermesh_spec import *
from Queue import Queue, Empty


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

class PowermeshPacket():
    """ Powermesh Packet
    """
    def __init__(self, phase, phy_rcv_valid, ppdu):
        self.phase = phase

        # PHY Layer
        self.phy_rcv_valid = phy_rcv_valid
        self.ppdu = ppdu

        # DLL Layer
        self.dll_rcv_valid = 0
        self.dll_rcv_indication = 0
        self.lpdu = []

        # APP Layer
        self.protocol = ''
        self.source_uid = [0,0,0,0,0,0]
        self.apdu = []
        self.app_rcv_indication = 0


    def abandon(self):
        """ abandon packet
        """
        self.phy_rcv_valid = 0
        self.dll_rcv_valid = 0
        self.dll_rcv_indication = 0



class Powermesh():
    '''A powermesh frame object
    '''


    def __init__(self, interface):
        """establish a powermesh obj by a frame of rcv_loop phy data or nothing('', for generate a phy frame)
        Params:
            interface: CV object handle
        """
        self.interface = interface
        self.plc_queue = Queue()
        self.broad_id = 1
        pass


    def get_plc_queue(self):
        return self.plc_queue


    def check_uid(self, packet):
        target_uid = packet.ppdu[SEC_DEST:SEC_DEST+6]
        if target_uid == [0,0,0,0,0,0] or target_uid == [0xff,0xff,0xff,0xff,0xff,0xff]\
            or target_uid == self.interface.cv_uid:
            return True
        else:
            return False


    def dll_rcv_proc(self, packet):
        if packet.phy_rcv_valid:
            phpr = packet.ppdu[SEC_PHPR]
            if phpr & 0x03 == FIRM_VER:
                if phpr & PHY_FLAG_SRF:
                    packet.dll_rcv_valid = BIT_DLL_VALID | BIT_DLL_ACK | BIT_DLL_SRF
                    packet.dll_rcv_indication = 1
                else:
                    dlct = packet.ppdu[SEC_DLCT]

                    if self.check_uid(packet):
                        if dlct & BIT_DLCT_DIAG:
                            #TODO:
                            pass
                        else:
                            if dlct & BIT_DLCT_ACK:
                                packet.dll_rcv_valid = BIT_DLL_VALID | BIT_DLL_ACK | (dlct & BIT_DLL_IDX)
                                packet.dll_rcv_indication = 1
                            else:
                                if dlct & BIT_DLCT_REQ_ACK:
                                    debug_output('req_ack packet received!')
                                    packet.abandon()
                                else:
                                    packet.dll_rcv_valid = BIT_DLL_VALID | (dlct & BIT_DLL_IDX)

                        if packet.dll_rcv_valid & BIT_DLL_VALID:
                            if packet.dll_rcv_valid & BIT_DLL_SRF:
                                packet.lpdu = packet.ppdu[1:-1]
                            else:
                                packet.lpdu = packet.ppdu[SEC_LPDU:-2]
                    else:
                        debug_output('packet target uid mismatch!')
                        packet.abandon()
            else:
                print "error FIRM_VER"
        return packet


    def nw_rcv_proc(self, packet):
        if packet.dll_rcv_valid and not packet.dll_rcv_valid & BIT_DLL_SRF:
            if not packet.lpdu[SEC_LPDU_DLCT] & BIT_DLCT_DIAG:
                nw_protocol_code = packet.lpdu[SEC_LPDU_PSR_ID] & 0xF0
                if nw_protocol_code == CST_PTP_PROTOCOL:
                    packet = self.ptp_rcv_proc(packet)
                # elif nw_protocol_code == CST_PSR_PROTOCOL:
                #     ##TODO: psr proc
                #     pass
                # elif nw_protocol_code == CST_DST_PROTOCOL:
                #     ##TODO: psr proc
                #     pass
                else:
                    print "error network protocol %x" % (nw_protocol_code,)
        return packet


    def ptp_rcv_proc(self, packet):
        if packet.dll_rcv_valid:
            packet.source_uid = packet.lpdu[SEC_LPDU_SRC : SEC_LPDU_SRC+6]
            packet.apdu = packet.lpdu[SEC_LPDU_PTP_APDU:]
            packet.protocol = 'PTP'
            packet.app_rcv_indication = 1
        return packet


    def app_rcv_proc(self, packet):
        pass


    def run_rcv_proc(self, rcv_body):
        packet = PowermeshPacket(rcv_body[0],rcv_body[1],rcv_body[2:])
        self.dll_rcv_proc(packet)
        self.nw_rcv_proc(packet)
        self.app_rcv_proc(packet)

        if packet.dll_rcv_indication or packet.app_rcv_indication:
            self.plc_queue.put(packet)
        else:
            print "discard packet:", packet

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

if __name__ == '__main__':
    from pvm_util import *
    pm = Powermesh(None)
    q = pm.get_plc_queue()

    # cv_input = '00006000FC3D25E2BC8834'
    # rcv_body = asc_hex_str_to_dec_array(cv_input)
    # pm.run_rcv_proc(rcv_body[3:-2])

    cv_input = '3118BDFFFFFFFFFFFF00570B0031004EF0000001020310A2'
    rcv_body = asc_hex_str_to_dec_array(cv_input)
    pm.run_rcv_proc(rcv_body)
    print dec_array_to_asc_hex_str(q.get().lpdu)