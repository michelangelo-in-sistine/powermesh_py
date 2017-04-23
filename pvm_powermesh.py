#!d:\\python27 python2.7
# -*- coding: cp936 -*-

import powermesh_rscodec
from pvm_util import *
from powermesh_spec import *
from Queue import Queue, Empty
from powermesh_timing import PowermeshTiming
import time

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
        self.source_uid = [0,0,0,0,0,0]
        self.target_uid = [0,0,0,0,0,0]

        # APP Layer
        self.protocol = ''
        self.apdu = []
        self.app_rcv_indication = 0


    def abandon(self):
        """ abandon packet
        """
        self.phy_rcv_valid = 0
        self.dll_rcv_valid = 0
        self.dll_rcv_indication = 0


class Powermesh_Dll_Send_Content():
    """
        Powermesh DLL Send需要的信息类
    """
    def __init__(self, target_uid, xmode, rmode, prop, lsdu):
        self.target_uid = target_uid
        self.xmode = xmode
        self.rmode = rmode
        self.prop = prop
        self.lsdu = lsdu

class Powermesh():
    '''A powermesh frame object
    '''


    def __init__(self, interface):
        """establish a powermesh process obj by a frame of rcv_loop phy data or nothing('', for generate a phy frame)
        Params:
            interface: CV object handle
        """
        self.interface = interface
        self.plc_queue = Queue()
        self.powermesh_timing = PowermeshTiming()
        self.last_broad_id = 0
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
                            if dlct & BIT_DLCT_ACK:						#
                                packet.dll_rcv_valid = BIT_DLL_VALID | BIT_DLL_DIAG | BIT_DLL_ACK | (dlct & BIT_DLL_IDX)
                                packet.dll_rcv_indication = 1
                            else:
                                # diag cv not response, just abondon it
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
                                packet.target_uid = packet.ppdu[SEC_DEST:SEC_DEST+6]
                                packet.source_uid = packet.ppdu[SEC_SRC:SEC_SRC+6]
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


    def powermesh_dll_single_transaction(self, dll_send_obj, check_fun, time_out, max_try = 1):
        """ dll层的收发控制
        Params:
            dll_send_obj: Powermesh_Dll_Send_Content类
            check_fun: 用于检查返回的函数
            timeout: 每一回合的定时时间
            max_try: 最大重试次数
        Returns:
            returned powermesh packet
        """
        assert isinstance(dll_send_obj, Powermesh_Dll_Send_Content), "error class type"

        if max_try > 0:
            ret = self.interface.dll_send(dll_send_obj.target_uid, dll_send_obj.lsdu, dll_send_obj.prop, dll_send_obj.xmode, dll_send_obj.rmode, delay = 0.02)
            time_remains = time_out
            if ret is not None:
                while time_remains > 0:
                    ret_packet, time_remains = self.interface.wait_a_plc_response(time_remains)
                    if ret_packet is not None:
                        if check_fun(dll_send_obj, ret_packet):
                            return ret_packet
                        else:
                            # if check_fun returns False, abondon current Packet
                            print 'error response abandoned, packet PPDU: ', dec_array_to_asc_hex_str(ret_packet.ppdu)
                            pass
            # if 1. CV Send Error 2. PLC timeout
            #    try once again by reentrance iteration
            return self.powermesh_dll_single_transaction(dll_send_obj, check_fun, time_out, max_try - 1)
        else:
            return


    def ebc_broadcast(self, broad_id, xmode = 0x80, rmode = 0x80, scan = 0, mask = 0, window = 5):
        """ 发broadcast帧, 返回接收的bsrf
        """

        lsdu = [EXP_EDP_EBC | (encode_xmode(rmode, scan) << 2) | EXP_EDP_EBC_NBF, broad_id<<4 | window, mask]
        prop = BIT_DLL_SEND_PROP_EDP | (BIT_DLL_SEND_PROP_SCAN if scan else 0)

        timeout = self.powermesh_timing.windows_delay_timing(4,rmode & 0x03,scan,window)
        self.interface.dll_send([0,0,0,0,0,0], lsdu, prop, xmode, rmode, delay = 0.02)
        time.sleep(timeout)

        bsrf_set = []
        while not self.plc_queue.empty():
            packet = self.plc_queue.get()
            if packet.dll_rcv_valid & BIT_DLL_SRF:
                bsrf_set.append(packet.ppdu[1:3])
        return bsrf_set


    def check_naf_return(self, dll_send_obj, ret_packet):
        try:
            if ret_packet.lpdu[SEC_LPDU_DLCT] & EXP_DLCT_EDP == EXP_DLCT_EDP:
                if ret_packet.lpdu[SEC_LPDU_NBF_CONF] & 0xC0 == EXP_EDP_EBC:
                    if ret_packet.lpdu[SEC_LPDU_NAF_CONF] & 0x03 == EXP_EDP_EBC_NAF:
                        if dll_send_obj.lsdu[SEC_LSDU_NIF_ID:SEC_LSDU_NIF_ID+2] == ret_packet.lpdu[SEC_LPDU_NAF_ID:SEC_LPDU_NAF_ID+2]:
                            # NIF_ID{7:4}:broad id, NIF_ID{3:0}+NIF_ID2: random id;
                            return True
        except Exception:
            pass
        return False


    def ebc_identify(self, bsrf_set, broad_id, xmode = 0x80, rmode = 0x80, scan = 0):
        """ 根据接收的bsrf id集合, 逐个identify得到uid
            返回uid集合
        """
        uid_set = []
        for bsrf_code in bsrf_set:
            debug_output('identify bsrf code:%s' % (bsrf_code,))
            lsdu = [EXP_EDP_EBC | (encode_xmode(rmode, scan) << 2) | EXP_EDP_EBC_NIF, broad_id<<4 | (bsrf_code[0] & 0x0F), (bsrf_code[1] & 0xFF)]
            prop = BIT_DLL_SEND_PROP_EDP | (BIT_DLL_SEND_PROP_SCAN if scan else 0)
            time_out = self.powermesh_timing.dll_ack_expiring_timing(len(lsdu) + LEN_TOTAL_OVERHEAD_BEYOND_LSDU, rmode&0x03, scan)
            dll_ebc_identify_obj = Powermesh_Dll_Send_Content([0,0,0,0,0,0],xmode,rmode,prop,lsdu)

            naf_packet = self.powermesh_dll_single_transaction(dll_ebc_identify_obj, self.check_naf_return, time_out, 2)
            if naf_packet is not None:
                uid_set.append(naf_packet.source_uid)
                # send confirm packet
                debug_output("confirm")
                lsdu = [EXP_EDP_EBC | EXP_EDP_EBC_NCF, broad_id<<4 | (bsrf_code[0] & 0x0F), (bsrf_code[1] & 0xFF)]  #不需要回应
                prop = BIT_DLL_SEND_PROP_EDP | (BIT_DLL_SEND_PROP_SCAN if scan else 0)
                self.interface.dll_send(naf_packet.source_uid, lsdu, prop, xmode, rmode, delay = 0.02)
                debug_output("wait %.2fs" % (self.powermesh_timing.dll_send_timing(len(lsdu),xmode&0x03,scan,0.02)))
                time.sleep(self.powermesh_timing.dll_send_timing(len(lsdu),xmode&0x03,scan,0.02))
        return uid_set



if __name__ == '__main__':
    from pvm_util import *
    pm = Powermesh(None)
    q = pm.get_plc_queue()

    # cv_input = '00006000FC25E2BC8834'
    # rcv_body = asc_hex_str_to_dec_array(cv_input)
    # pm.run_rcv_proc(rcv_body[3:-2])

    cv_input = '3118BDFFFFFFFFFFFF00570B0031004EF0000001020310A2'
    rcv_body = asc_hex_str_to_dec_array(cv_input)
    pm.run_rcv_proc(rcv_body)
    print dec_array_to_asc_hex_str(q.get().lpdu)