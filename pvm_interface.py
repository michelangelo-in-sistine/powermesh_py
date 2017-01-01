#!d:\\python27 python2.7
# -*- coding: cp936 -*-
# author: Lv Haifeng
# ver: 1.0
# 2016-10-18
# TODO: 1. caculated transaction timeout
#       2. ebc broadcast

from serial import Serial, SerialException
from threading import Thread
import time
from pvm_util import *
from pvm_powermesh import *
from Queue import Queue, Empty
import re
import sys


class PvmFatalException(Exception):
    """ The exceptions when raised the whole process should quit
    """
    pass

class PvmException(Exception):
    """ all exceptions when raised means small mistake
        e.g. the current node transaction should be broken or retry
        but the next node should start
    """
    EXCEPT_CODE_SS_HARDFAULT = 0x81         # SSӲ������NVR��д����
    EXCEPT_CODE_SS_FORMAT_ERR = 0x82        # SS�����ʽ����, ��Ƿ�������
    EXCEPT_CODE_SS_EXEC_ERR = 0x83          # SSִ�д���, ��û��ָ���Ķ�������
    EXCEPT_CODE_SS_AUTHORITY_ERROR = 0x84	# SS��ȫ����, ���������

    EXCEPT_CODE_CMD_ERR = 0x8A              # CV��ʾ��֧�ִ�����0
    EXCEPT_CODE_FORMAT_ERR = 0x8B           # CV��ʾ����֡�����ʽ����
    EXCEPT_CODE_DIAG_FAIL = 0x8C            # Diag Time Out
    EXCEPT_CODE_RETURN_FROMAT_ERR = 0x8D    # CV���ص�����֡��ʽ����, ����CRC����
    EXCEPT_CODE_TIME_OUT = 0x8E             # ��ʱ

    def __init__(self, except_code, msg = ''):
        Exception.__init__(self,msg)
        self.except_code = except_code

## ACP Protocol constants
ACP_IDTP_DB = 0             #��㲥
ACP_IDTP_VC = 1             #����ͨ��
ACP_IDTP_MC = 2             #��㳭��
ACP_IDTP_GB = 3             #�����
SECURITY_CODE_HIGH8 = 0x95
SECURITY_CODE_LOW8 = 0x27
SECURITY_CODE_HEX_FORMAT = dec_array_to_asc_hex_str([SECURITY_CODE_HIGH8, SECURITY_CODE_LOW8])

class CV(object):
    """\
    Create a layer object between CV device and transaction entity
    """
    #
    CV_FUNC_CODE_READ_UID = 0x01
    CV_FUNC_CODE_NOTIFY_ADDR = 0x02
    CV_FUNC_CODE_READ_PHY_REG = 0x03
    CV_FUNC_CODE_WRITE_PHY_REG = 0x04
    CV_FUNC_CODE_SET_INDICATION_LEVEL = 0x05   # TBD
    CV_FUNC_CODE_PHY_SEND = 0x10
    CV_FUNC_CODE_DLL_SEND = 0x11
    CV_FUNC_CODE_DIAG = 0x12
    CV_FUNC_CODE_PLC_INDICATION = 0x20

    ACP_FUNC_CODE_SET_ADDR = 0x01           # ����ACP��ַ
    ACP_FUNC_CODE_READ_PARA = 0x02          # ��ȡģ�鵱ǰ����
    ACP_FUNC_CODE_FRAZ_PARA = 0x03          # ����ģ�鵱ǰ����

    ACP_FUNC_CODE_CALIB_PARA = 0x0C         # ģ��У׼

    PARA_VOLTAGE = 0x01
    PARA_CURRENT = 0x02
    PARA_TEMPERATURE = 0x04


    def __init__(self, port, baudrate = 115200):
        self.init = False
        self.port_on = False
        self.cv_uid_crc = [0, 0]
        self.powermesh = Powermesh(self)

        try:
            self.ser = Serial(port, baudrate = baudrate, bytesize=8, parity='N', stopbits=1)
            self.com = port
            self.baudrate = baudrate
            debug_output('%s open successfully' % self.com)
            self.port_on = True

            ## �����߳�����
            self.rcv_loop_thread = None         # All property should be initialized in __init__()
            self.rcv_loop_thread_on = False
            self.start_rcv_loop_thread()

            self.cv_queue = Queue()
            self.plc_queue = self.powermesh.get_plc_queue()     # PLC���յ���һ������
            self.init = True

            # acp init
            self.set_xmode()
            uid = self.read_uid()
            if uid:
                self.cv_uid = uid
                self.cv_uid_crc = crc16(uid)
                debug_output('set cv domain id as ' + dec_array_to_asc_hex_str(self.cv_uid_crc))
                self.set_domain_id(self.cv_uid_crc)       # ��ʼ��ID
            else:
                raise PvmFatalException('cv uid read fail! check RS485 connection!')
            self.set_self_vid()

        except SerialException:
            debug_output("%s open fail!" % port)
            raise SerialException
        except Exception as err:
            self.close()
            print str(err)
            raise err


    # def __del__(self):
    #     """
    #         __del__()ֻ���������ڲ���Ա��û�б����õ�ʱ��ű����ã����������˵������ser�رգ�rcv_loop�˳�
    #         ���__del__()������������ʵ���õ�quit_rcv_loop_thread()��ser.close()�������õ�
    #         ��Ϊ�������������������Ļ���__del__()�����������ᱻִ��
    #
    #         �������ĵ���Ҫ�����㣺1��uart io�ڱ�ռ���޷��ٴδ� 2��������rcv_loop_thread()�̲߳��ܽ���������ѭ��
    #         ʵ��֤ʵ��������������µ���python xxx.pyִ�е�python����
    #         ���������������python����ǿ�йر�
    #         ��Ȼ�������__del__()����
    #         ��uart io��رգ�rcv_loop_thread�����߳�Ҳ�ᱻ����
    #
    #         �������赣��
    #     """
    #     debug_output("eliminate Interface object")
    #     try:
    #         self.quit_rcv_loop_thread()         # �����߳̽���
    #         self.ser.close()
    #     except Exception as e:
    #         debug_output("except happened when Interface object destructed!")
    #         print e


    def is_open(self):
        return self.port_on


    def open(self):
        if not self.port_on:
            self.ser.open()
            self.port_on = True

            ## �����߳�����
            self.start_rcv_loop_thread()

        else:
            debug_output("Port has been already opened")


    def close(self):
        if self.port_on:
            debug_output('interface turn off')
            self.quit_rcv_loop_thread()      # �����߳̽���
            self.ser.close()
            self.port_on = False
        else:
            debug_output("Port has been already closed")


    def rcv_loop(self):
        ## ����CV�����ı��Ķ����߳�
        ## �з���CVͨ��Э��������������Queue��
        self.rcv_loop_thread_on = True
        rcv_data = ''
        rcv_bytes = 0

        while self.rcv_loop_thread_on:
            try:
                if self.ser.inWaiting() != rcv_bytes:
                    rcv_bytes = self.ser.inWaiting()        # receving status
                else:
                    if rcv_bytes:
                        temp = self.ser.read(rcv_bytes)
                        #sys.stdout.write(temp)
                        # debug_output(temp)
                        rcv_data += temp # ����ȡ����״̬����
                        rcv_bytes = 0

                        # �����Ч�Ľ��ղ��������Queue��
                        match_rslt = re.findall(r'<(\w+)>',rcv_data)
                        if match_rslt:
                            for item in match_rslt:
                                debug_output('<= <' + item + '>')
                                if item[4:6] == '60' and hasattr(self,'powermesh'):
                                    ret_func_code, body = self.parse_return(item)
                                    self.powermesh.run_rcv_proc(body)
                                else:
                                    self.cv_queue.put(item)
                            index = rcv_data.rfind(match_rslt[-1]) + len(match_rslt[-1]) + 1    #
                            rcv_data = rcv_data[index:]
                time.sleep(0.01)
            except SerialException:
                debug_output('Comm Object is Cleared')
                self.rcv_loop_thread_on = False
                self.cv_queue.put(None)
                break
            except PvmException as pe:
                print "rcv loop thread PvmException!"
                print str(pe)
                break
        debug_output('rcv loop thread quit')


    def start_rcv_loop_thread(self):
        self.rcv_loop_thread = Thread(target = self.rcv_loop)
        self.rcv_loop_thread.start()


    def quit_rcv_loop_thread(self):
        self.rcv_loop_thread_on = False


    def get_queue(self):
        ## get handle of queue
        return self.cv_queue


    # def write(self, write_str):
    #     """ send 'write_str' to uart port as what it is"""
    #     self.ser.write(write_str)
    #
    #
    # def send(self, decimal_array):
    #     """ convert decimal_array as hex str included with a pair of '<' and '>', and send it to uart port
    #     Params:
    #         data: a list of DECIMAL BYTE DATA
    #     Output to cv:
    #         '<ASC_HEX_STR>'
    #     """
    #     if self.port_on:
    #         self.ser.write('<' + dec_array_to_asc_hex_str(decimal_array) + '>')
    #     else:
    #         print('port is not opened')


    def send_cv_a_frame(self, frame):
        """
            ��cv����һ֡���� ��ʽ <ADDR_H ADDR_L FUNC_CODE BODY CRC_H CRC_L>
        Params:
            frame: ��<ASC HEX STR>��/ASC HEX STR/ DECIMAL BYTE LIST
        Output to cv:
            '<ASC_HEX_STR>'
        Return:
            cv frame func_code
        """
        if not self.port_on:
            print('port is not opened')
            return
        else:
            if type(frame) == str:
                if frame[0] == '<' and frame[-1] == '>':
                    assert len(frame) >= 12, 'not enough frame length' # <addr_h,addr_l,func_code,crc_h,crc_l> at least 12 bytes
                else:
                    assert len(frame) >= 10, 'not enough frame length'
                    frame = '<' + frame + '>'
                func_code = int(frame[5:7] ,16)
            else:
                func_code = frame[2]
                frame = '<' + dec_array_to_asc_hex_str(frame) + '>'
            debug_output('=> ' + frame)
            self.ser.write(frame)
            return func_code


    def wait_a_response(self, queue_handle, timeout):
        """ �ȴ�һ�����е���Ӧ����ʱ�յ���Ӧ���أ���Ӧ����ʣ��ʱ�䣩����ʱ����(None, 0)
        Params:
            queue_handle: ������cv���У�Ҳ������plc����
            timeout: ���ȴ�ʱ��
        """
        ct = time.clock()
        try:
            ret = queue_handle.get(timeout = timeout)
            return ret, timeout + ct - time.clock()
        except Empty:
            return None, 0       # Ϊ�˴���index����һ��


    def wait_a_cv_response(self, timeout):
        """
            in case of the return of  is not what you are waiting for,
            you can start another waiting by this function, and just input the returned timeout remains to it
            ���single_response_transaction()�õ��Ĳ�����ȷ�ķ��أ����Ե��ô˺�����ʼ�µĵȴ�
            ��ֻ�轫�ϴη��ص�ʣ��timeoutʱ�䴫�뼴��
        """
        return self.wait_a_response(self.cv_queue, timeout)


    def parse_return(self, cv_frame):
        """
            ���cv�ķ���
            ��retΪNone, raise PvmException with TimeOut error code
            ��ret������crcҪ��raise PvmException with EXCEPT_CODE_FORMAT_ERR error code
            ��ret������һ��exception֡��raise PvmException with its error code
            ��ret����������([addr_h, addr_l], func_code, body)
        """

        # Check validility
        if cv_frame is None:
            raise PvmException(PvmException.EXCEPT_CODE_TIME_OUT, 'cv response time out')

        cv_frame = asc_hex_str_to_dec_array(cv_frame)

        if len(cv_frame) < 5:
            raise PvmException(PvmException.EXCEPT_CODE_FORMAT_ERR, 'bad cv frame length')

        if crc16(cv_frame) != [0xE2, 0xF0]:
            raise PvmException(PvmException.EXCEPT_CODE_FORMAT_ERR, 'crc error')

        addr = cv_frame[0:2]
        func_code = cv_frame[2]
        body = cv_frame[3:-2]

        if addr != [0, 0] and addr != self.cv_uid_crc:
            raise PvmException(PvmException.EXCEPT_CODE_FORMAT_ERR, 'error cv uid address: ' + str(addr))

        if func_code & 0x80:
            raise PvmException(func_code, 'WARNING!\nCV RETURN EXCEPTION')

        if func_code & 0x40:
            return func_code, body
        else:
            raise PvmException(PvmException.EXCEPT_CODE_FORMAT_ERR, 'direction bit flag is not set')


    def single_cv_response_transaction(self, frame, time_remains = 1):
        """
            ��cv����һ֡��� ���ڴ���timeout����λ���룩ʱ����cv��һ�η���
            ��鷵��֡�ĸ�ʽ, Ҫ���ʽ��ȷ��CRC��ȷ����ַ��ȷ, ��������ȷ
        Params:
            send_cmd: ��cv���͵������ʽ ��<ASC HEX STR>�� �� decimal byte list
            timeout:  ���ȴ�ʱ��
        Return:
            cv��������������
            or
            None (if timeout)
            2016-11-12 CV��ʱ������Exception, ������Ҫ������������
        """
        func_code = self.send_cv_a_frame(frame)
        while time_remains > 0:
            ret_frame, time_remains = self.wait_a_cv_response(time_remains)
            if ret_frame is not None:
                ret_func_code, body = self.parse_return(ret_frame)
                if func_code & 0x3F == ret_func_code & 0x3F:
                    return body
                else:
                    debug_output('got a un-expected response')
                    debug_output(dec_array_to_asc_hex_str(ret_frame))
                    pass                # TBD proceed unexpected frame
        return None


    def multiple_response_transaction(self, frame, timeout):
        """
            ��cv����һ֡��� ���ռ�����cv�ķ���, ����һ�����յĳ�����
        Params:
            send_cmd: ��cv���͵������ʽ ��<ASC HEX STR>�� �� decimal byte list
            timeout:  �ȴ�ʱ��
        Returns:
            A list consisted of returned frame, maybe empty if no frame returned
        """
        self.send_cv_a_frame(frame)
        ret = []
        ct = time.clock()
        while time.clock() - ct < timeout:
            if self.cv_queue.qsize() > 0:
                ret.append(self.cv_queue.get())
        return ret


    def gen_fpu_to_cv_frame(self, func_code, body = []):
        """
            ����fpu����cv������֡
        Params:
            func_code: ������
            target_addr: CV UID��CRC, 0x0000Ϊͨ���ַ
        Return:
            decimal list
        """

        frm = self.cv_uid_crc + [func_code] + body
        frm += crc16(frm)
        return frm

    ## CV Transaction
    def read_uid(self):
        """ ��ȡcv��uid, �ɹ��򷵻�target uid ������cv_uid crc, ʧ���򷵻�None
            ���ô�������uart����
        Params:
            No
        Returns:
            uid(dec byte list)
        Exception:
            PvmException(Error_Code, Msg)
        """
        frm = self.gen_fpu_to_cv_frame(CV.CV_FUNC_CODE_READ_UID)
        uid = self.single_cv_response_transaction(frm)
        return uid


    def diag(self, target_uid, xmode = 0x10, rmode = 0x10, scan = 0x01):
        """ diag a module by uid formated as an ascii hex str
        Params:
            target_uid: an 12-byte asc hex str, e.g. '5e1d0a05ff', OR 6 byte decimal byte list
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
                ch scan mode, 01 = True, 00 = False;
        """

        if type(target_uid) == str:
            assert len(target_uid) == 12, 'error target uid length: %s' % target_uid
            target_uid = asc_hex_str_to_dec_array(target_uid)
        assert len(target_uid) == 6, 'error target uid length: %s' % target_uid

        frm = self.gen_fpu_to_cv_frame(CV.CV_FUNC_CODE_DIAG, target_uid + [xmode, rmode, scan])
        try:
            result = self.single_cv_response_transaction(frm, 5)

            if result:
                rate_map = {0x00:'BPSK',0x01:'DS15',0x02:'DS63'}
                result = [item if item <128 else item - 256 for item in result]
                down_result=[]
                up_result=[]
                if scan:
                    for i in range(4):
                        down_result.append([result[i*2], result[i*2+1]])
                        up_result.append([result[i*2+8], result[i*2+9]])
                else:
                    p = 0
                    for i in range(4):
                        if xmode & (0x10<<i):
                            down_result.append([result[p*2], result[p*2+1]])
                            p += 1
                        else:
                            down_result.append(['NA', 'NA'])


                    for i in range(4):
                        if rmode & (0x10<<i):
                            up_result.append([result[p*2], result[p*2+1]])
                            p += 1
                        else:
                            up_result.append(['NA', 'NA'])

                print 'DIAG RESULT:'
                print 'TARGET UID:%s' % dec_array_to_asc_hex_str(target_uid)
                print '-------------------------------------------------'
                print '\t\tDOWNLINK(%s)\t\t\tUPLINK(%s)' % (rate_map[xmode&0x0F], rate_map[rmode&0x0F])
                print '\t\tSS(dBuV)\tSNR(dB)\t\tSS(dBuV)\tSNR(dB)'
                for i in range(4):
                    print 'CH%d:\t%s\t\t\t%s\t\t\t%s\t\t\t%s' % (i,down_result[i][0],down_result[i][1],up_result[i][0],up_result[i][1])


            return result
        except PvmException as pe:
            print str(pe)


    def phy_send(self, psdu, xmode=0x80, scan = False, srf = False, ac_update = False, delay = 0):
        """ ����cv����phy֡
            format: 1B phase, 1B psdu_len, 1B xmode, 1B prop, 4B delay, NB psdu
        Params:
            psdu: ����֡�壬������decimal byte list
            xmode: ��4λ��Ƶ��, ��2λ������
                    0x1X: CH0   0xX0: BPSK
                    0x2X: CH1   0xX1: DS15
                    0x4X: CH2   0xX2: DS63
                    0x8X: CH3
                    0xFX: SALVO
            scan:
            srf:
            ac_update:
            delay:  �ӳٷ��͵ĺ�����
        """
        assert (xmode & 0xF0 in (0x10, 0x20, 0x40, 0x80, 0xF0) and xmode % 4 in (0x00, 0x01, 0x02)), "error xmode 0x%02X" % xmode
        assert len(psdu) <= 300, "error phy len %d" % len(psdu)

        phase = [0]
        psdu_len = [len(psdu)]
        prop = [(0x08 if scan else 0) \
                | (0x04 if srf else 0) \
                | (0x01 if ac_update else 0)]
        delay_list = asc_hex_str_to_dec_array('%08X' % (delay))

        frm = self.gen_fpu_to_cv_frame(CV.CV_FUNC_CODE_PHY_SEND, phase + psdu_len + [xmode] + prop + delay_list + psdu)
        return self.single_cv_response_transaction(frm)


    def dll_send(self, target_uid, lsdu, prop = 0, xmode = 0x80, rmode = 0x80, delay=0):
        """ ����cv����dll֡
            format: 1B phase, 1B lsdu_len, 6B uid, 1B prop, 1B xmode, 1B rmode, 4B delay, NB lsdu
        Params:
            lsdu: ������decimal byte list
            target_uid: ������12�ֽ�str��6�ֽ�decimal byte list
            prop: [DIAG ACK REQ_ACK EDP_PROTOCAL SCAN SRF 0 ACUPDATE]
            xmode: ����ģʽ
            rmode: ������diag��ebcʱ����
        """

        if type(target_uid) == str:
            assert len(target_uid) == 12, 'error target uid length: %s' % target_uid
            target_uid = asc_hex_str_to_dec_array(target_uid)
        assert len(target_uid) == 6, 'error target uid length: %s' % target_uid

        assert (xmode & 0xF0 in (0x10, 0x20, 0x40, 0x80, 0xF0) and xmode % 4 in (0x00, 0x01, 0x02)), "error xmode 0x%02X" % xmode
        assert (rmode & 0xF0 in (0x10, 0x20, 0x40, 0x80, 0xF0) and rmode % 4 in (0x00, 0x01, 0x02)), "error rmode 0x%02X" % rmode

        phase = [0]
        lsdu_len = [len(lsdu)]
        delay_list = asc_hex_str_to_dec_array('%08X' % (delay))

        frm = self.gen_fpu_to_cv_frame(CV.CV_FUNC_CODE_DLL_SEND, phase + lsdu_len + target_uid + [prop, xmode, rmode] + delay_list + lsdu)
        return self.single_cv_response_transaction(frm)


    def app_send(self, apdu, protocol = 'ptp', target_uid = 'ffffffffffff', xmode = None):
        if protocol == 'ptp':
            if xmode is None:
                xmode = self.xmode
            lsdu = [0xF0, 0x00] + apdu
            return self.dll_send(target_uid,lsdu,xmode=xmode)


    ## PLC Transaction Functions
    def wait_a_plc_response(self, timeout):
        """
        �ȴ�PLC���еķ���
        """
        return self.wait_a_response(self.plc_queue, timeout)


    def set_domain_id(self, domain_id):
        """ ����acp����id, ȱʡ����¾���cv uid��CRCֵ
        """
        self.domain_id_high8 = domain_id[0]
        self.domain_id_low8 = domain_id[1]
        self.domain_id = self.domain_id_high8 * 256 + self.domain_id_low8


    def set_self_vid(self, self_vid = 1):
        """ ����cv��acp��vid��ȱʡ����Ϊ1, ����SSΪ������Ȼ��
        """
        self.self_vid = self_vid


    def set_xmode(self, default_xmode = 0x80):
        self.xmode = default_xmode


    def acp_send(self, acp_body, idtp, target_uid = 'ffffffffffff', req = 1, domain_id = [0, 0], vid = 0, start_vid = 0, end_vid = 0, gid = 0):
        """ ACP Protocl Packet
        Params:
            acp_body: ������
            idtp: ͨ�ŵ�ַ����
                ACP_IDTP_DB: ��㲥
                ACP_IDTP_VC: �㲥
                ACP_IDTP_MC: �ಥ
                ACP_IDTP_GC: �鲥
            domain_id: ���ַ, ��ʽΪ�����ֽڵ�list
            vid: int
            req: ��Ҫ�ظ�
        Returns:
            ���������ɣ�����tran_id
            ���򷵻�None
        """
        apdu = [0x18]
        if not hasattr(self, 'acp_tran_id'):
            self.acp_tran_id = 0

        apdu += [(idtp<<5) | self.acp_tran_id, domain_id[0], domain_id[1]]

        if idtp == ACP_IDTP_DB:
            pass
        elif idtp == ACP_IDTP_VC:
            apdu += [(vid >> 8) % 256, vid % 256]
        elif idtp == ACP_IDTP_MC:
            apdu += [(start_vid >> 8) % 256, start_vid % 256, (end_vid >> 8) % 256, end_vid % 256, (self.self_vid >> 8) % 256, self.self_vid % 256]
        else:
            apdu += [(gid >> 8) % 256, gid % 256]

        if req:
            acp_body[0] = acp_body[0] | 0x40     # acp body��һ�ֽ�Ϊcommand, ��6λΪreq

        apdu += acp_body
        apdu.append(calc_cs(apdu))

        if self.app_send(apdu,'ptp',target_uid):
            temp = self.acp_tran_id
            self.acp_tran_id = (self.acp_tran_id + 1 ) % 0x10
            return temp
        else:
            return None


    def single_acp_transaction(self, acp_body, idtp, time_remains, target_uid = 'ffffffffffff', domain_id = [0, 0], vid = 0):
        """ ͨ��plcͨ�ţ�FPU����CVʵ�����ض���һ��SSʹ��acpЭ�顰һ��һ��.
            ����ʹ��uid, ��ʹ��vidѰַ��ǰ����������δ����vidʱ�ĵ�ַ���ã�У׼�ȹ����������ʺ��ֳ�������
        Params:
            ��
        Returns��
            ��ͨ�ų�ʱ������None; ��ͨ������������acp_body
        """
        assert idtp == ACP_IDTP_DB or idtp == ACP_IDTP_VC, 'idtp must be DB or VC, not %d' % (idtp,)

        tran_id = self.acp_send(acp_body, idtp, target_uid, req = 1, domain_id = domain_id, vid = vid)
        if tran_id is not None:
            while time_remains > 0:
                powermesh_packet, time_remains = self.wait_a_plc_response(time_remains)
                if powermesh_packet is not None:
                    ret = self.check_acp_return(acp_body, idtp, target_uid, domain_id, vid, tran_id, powermesh_packet)
                    if ret:
                        debug_output(dec_array_to_asc_hex_str(powermesh_packet.apdu))
                        debug_output('transaction time_remains :%.2f' % time_remains)
                        return ret
        else:
            debug_output('acp send Fail')
            return None
        debug_output('single acp transaction timeout')
        return None         # time out


    def check_acp_return(self, acp_body, idtp, target_uid, domain_id, vid, tran_id, powermesh_packet):
        """ ��鷵�ص�acp������Ч��

        Returns��
            ������ص�powermesh�����ǵ�ǰtransaction����ȷ���أ�����acp_body����
            ������ǵ�ǰ���ģ�����None

        """
        if powermesh_packet.apdu[0] != 0x18:
            debug_output('not a acp frame')
            return None            # ����acp֡

        if sum(powermesh_packet.apdu) % 256 != 0:
            debug_output('acp check sum not match')
            return None            # acp֡У��Ͳ�Ϊ0

        return_idtp = (powermesh_packet.apdu[1] & 0x60) >> 5
        return_follow = (powermesh_packet.apdu[1] & 0x10)
        return_tran_id = (powermesh_packet.apdu[1] & 0x0F)
        return_domain_id_high8 = powermesh_packet.apdu[2]
        return_domain_id_low8 = powermesh_packet.apdu[3]

        if not return_follow:
            debug_output('not a follow frame')
            return None            # ���Ƿ��ص�֡

        if return_tran_id != tran_id:
            debug_output('tran_id not match')
            return None            # ���ص�֡���кŲ�ƥ��

        if return_idtp != idtp:
            debug_output('idtp not match')
            return None            # ���ص�֡��ַ���Ͳ�ƥ��

        if domain_id != [0, 0] and domain_id != [return_domain_id_high8, return_domain_id_low8]:
            debug_output('Domain mismatch')
            return None        # domain mismatch

        if idtp == ACP_IDTP_DB:
            if target_uid.lower() != 'ffffffffffff':
                if asc_hex_str_to_dec_array(target_uid) != powermesh_packet.source_uid:
                    debug_output('uid mismatch')
                    return None    # uid mismatch
            body_index = 4
        elif idtp == ACP_IDTP_VC:
            return_vid = powermesh_packet.apdu[4]*256 + powermesh_packet.apdu[5]
            if vid != 0 and vid != return_vid:
                debug_output('vid mismatch')
                return None
            body_index = 6

        return_acp_cmd = powermesh_packet.apdu[body_index]
        if return_acp_cmd & 0x80:
            raise PvmException(return_acp_cmd, "WARNING!SS RETURN EXCEPTION! CODE %02X" % return_acp_cmd)
        elif return_acp_cmd != (acp_body[0] & 0xBF) | 0x20:
            debug_output('cmd code not match')
            return None

        # All parse
        return powermesh_packet.apdu[body_index + 1 : -1]


    def inquire_ss_acp_addr(self, target_uid):
        """ ͨ��UIDָ��һ��SS, ��ѯ��domain id�� vid�� gid��ַ
        """
        debug_output('====\nInquire addr of SS[%s]:' % target_uid)
        acp_frame = [CV.ACP_FUNC_CODE_SET_ADDR] + asc_hex_str_to_dec_array('ffff ffff ffff ' + SECURITY_CODE_HEX_FORMAT)
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_DB, time_remains=2, target_uid=target_uid)
        if ret:
            debug_output('SS [%s]:\nDOMAIN:%04X\nVID:%04X\nGID:%04X' % (target_uid, \
                                                                        ret[0]*256 + ret[1],\
                                                                        ret[2]*256 + ret[3],\
                                                                        ret[4]*256 + ret[5]))
            return ret


    def set_ss_acp_addr(self, target_uid, vid, domain_id = None, gid=0xffff):
        """ ͨ��UIDָ��һ��SS, ����vid, domain_id, gid
        """
        debug_output('====\nSet addr of SS[%s]:' % target_uid)
        if domain_id is not None:
            hex_domain_id = '%04X' % (domain_id,)
        else:
            hex_domain_id = 'ffff'
        hex_vid = '%04X' % (vid,)
        hex_gid = '%04X' % (gid,)

        acp_frame = [CV.ACP_FUNC_CODE_SET_ADDR] + asc_hex_str_to_dec_array(hex_domain_id + hex_vid + hex_gid + SECURITY_CODE_HEX_FORMAT)
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_DB, time_remains=2, target_uid = target_uid)
        if ret:
            return ret
        else:
            print 'uid [%s] addr set fail' % target_uid


    def read_ss_current_parameter_by_uid(self, target_uid, parameter_code = 0x07):
        """ ����uidѰַ����ģ�鵱ǰ����
        Params:
            uid: ģ��UID, 'FFFFFFFFFFFF'Ϊͨ��UID��ַ
            parameter_code: CV.PARA_VOLTAGE(��ѹ) | CV.PARA_CURRENT(����) | CV.PARA_TEMPERATURE(�¶�), ����"|"�����������
        Returns:
            tuple of call-for parameters
            ע�⣺���ز�����˳���� ���¶ȣ�����У�������������У�����ѹ������У���
        """
        debug_output('====\nRead parameter of SS[%s], para code %02X:' % (target_uid,parameter_code))
        acp_frame = [CV.ACP_FUNC_CODE_READ_PARA, parameter_code]
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_DB, time_remains=5, target_uid = target_uid)
        if ret:
            paras = [ret[2*i]*256+ret[2*i+1] for i in range(len(ret)/2)]
            paras = [item if item <32768 else item - 65536 for item in paras]

            debug_output('CURRENT PARAMETERS of SS[%s]' % uid)
            i = 0
            if parameter_code & CV.PARA_TEMPERATURE:
                paras[i] = paras[i] * 1.0 / 100
                debug_output('TEMPERATURE:%.2f' % paras[i])
                i += 1

            if parameter_code & CV.PARA_CURRENT:
                paras[i] = paras[i] * 1.0 / 1000
                debug_output('CURRENT:%.2f' % paras[i])
                i += 1

            if parameter_code & CV.PARA_VOLTAGE:
                paras[i] = paras[i] * 1.0 / 100
                debug_output('VOLTAGE:%.2f' % paras[i])

            return tuple(paras)

        else:
            print 'uid [%s] read parameter fail' % target_uid


    def read_ss_current_parameter_by_vid(self, target_vid, parameter_code = 0x07):
        """ ����vidѰַ����ģ�鵱ǰ����
        Params:
            vid: ���õ�vid��ַ
            parameter_code: CV.PARA_VOLTAGE(��ѹ) | CV.PARA_CURRENT(����) | CV.PARA_TEMPERATURE(�¶�), ����"|"�����������
        Returns:
            tuple of call-for parameters
            ע�⣺���ز�����˳���� ���¶ȣ�����У�������������У�����ѹ������У���
        """
        debug_output('====\nRead parameter of SS[vid = 0x%04X], para code %02X:' % (target_vid, parameter_code))
        acp_frame = [CV.ACP_FUNC_CODE_READ_PARA, parameter_code]
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_VC, time_remains=4, domain_id = [self.domain_id_high8, self.domain_id_low8], vid = target_vid)
        if ret:
            paras = [ret[2*i]*256+ret[2*i+1] for i in range(len(ret)/2)]
            paras = [item if item <32768 else item - 65536 for item in paras]

            debug_output('CURRENT PARAMETERS of SS[%s]' % uid)
            i = 0
            if parameter_code & CV.PARA_TEMPERATURE:
                paras[i] = paras[i] * 1.0 / 100
                debug_output('TEMPERATURE:%.2f' % paras[i])
                i += 1

            if parameter_code & CV.PARA_CURRENT:
                paras[i] = paras[i] * 1.0 / 1000
                debug_output('CURRENT:%.2f' % paras[i])
                i += 1

            if parameter_code & CV.PARA_VOLTAGE:
                paras[i] = paras[i] * 1.0 / 100
                debug_output('VOLTAGE:%.2f' % paras[i])

            return tuple(paras)

        else:
            print 'vid [%04X] read parameter fail' % target_vid


    def calib_ss_voltage_by_uid(self, target_uid, index, set_voltage_value):
        """ ͨ��PLC��У��ָ��ģ��ĵ�ѹ����ֵ
        Params��
            uid: ҪУ��ģ���uid�� ����ʹ��ȫFFͨ��UID��ַ
            index: must be 0 or 1; when 0, calib the first point, when 1, calib the second point and calculate coefficients
            set_voltage: ��֪SS��ǰ��׼ȷ������ѹֵ, ������, ������λС��
        """
        assert index == 0 or index == 1, "index must be either 0 or 1"
        assert 0 <= set_voltage_value <= 80, "calib set voltage must be a valid value"
        debug_output('====\nCalib SS[%s]' % target_uid)

        value = int(set_voltage_value * 100)
        acp_frame = [CV.ACP_FUNC_CODE_CALIB_PARA, ord('U'), index, value>>8, value % 256, SECURITY_CODE_HIGH8, SECURITY_CODE_LOW8]
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_DB, time_remains=4, target_uid = target_uid)
        if ret:
            return ret
        else:
            debug_output('SS Module[%s] voltage calibration failed' % target_uid)


    def calib_ss_current_by_uid(self, target_uid, index, set_current_value):
        """ ͨ��PLC��У��ָ��ģ��ĵ�������ֵ
        Params��
            uid: ҪУ��ģ���uid�� ����ʹ��ȫFFͨ��UID��ַ
            index: must be 0 or 1; when 0, calib the first point, when 1, calib the second point and calculate coefficients
            set_current: ��֪SS��ǰ��׼ȷ��������ֵ, ������, ����3λС��
        """
        assert index == 0 or index == 1, "index must be either 0 or 1"
        assert 0 <= set_current_value <= 20, "calib set current must be a valid value"
        debug_output('====\nCalib SS[%s]' % target_uid)

        value = int(set_current_value * 1000)
        acp_frame = [CV.ACP_FUNC_CODE_CALIB_PARA, ord('I'), index, value>>8, value % 256, SECURITY_CODE_HIGH8, SECURITY_CODE_LOW8]
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_DB, time_remains = 4, target_uid = target_uid)
        if ret:
            print ret
        else:
            debug_output('SS Module[%s] current calibration failed' % target_uid)


    def calib_ss_temperature_by_uid(self, target_uid, index, set_current_voltage):
        """ ͨ��PLC��У��ָ��ģ����¶Ȳ���ֵ
            SSģ����¶�У���Ƕ��¶ȵ�·���ض���ѹУ������У���ģ�һ�����У������0.5V��4.5V��ѹ
        Params��
            uid: ҪУ��ģ���uid�� ����ʹ��ȫFFͨ��UID��ַ
            index: must be 0 or 1; when 0, calib the first point, when 1, calib the second point and calculate coefficients
            set_current_voltage: ��֪SS��ǰ��У����׼ȷ������ѹֵ, ������, ����2λС��
        """
        assert index == 0 or index == 1, "index must be either 0 or 1"
        assert 0 <= set_current_voltage <= 6, "calib set value must be a valid value"
        debug_output('====\nCalib SS[%s]' % target_uid)

        value = int(set_current_voltage * 100)
        acp_frame = [CV.ACP_FUNC_CODE_CALIB_PARA, ord('T'), index, value>>8, value % 256, SECURITY_CODE_HIGH8, SECURITY_CODE_LOW8]
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_DB, time_remains = 4, target_uid = target_uid)
        if ret:
            print ret
        else:
            debug_output('SS Module[%s] temperature calibration failed' % target_uid)


    def save_ss_calib_by_uid(self, target_uid):
        """ ��У����ϵ�����浽NVR
        """
        debug_output('====\nCalib SS[%s]' % target_uid)
        acp_frame = [CV.ACP_FUNC_CODE_CALIB_PARA, ord('S'), SECURITY_CODE_HIGH8, SECURITY_CODE_LOW8]
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_DB, time_remains = 4, target_uid = target_uid)
        if ret:
            debug_output('SS Module[%s] calib saved' % target_uid)
        else:
            debug_output('SS Module[%s] save calibration failed' % target_uid)


    def reset_ss_by_uid(self, target_uid):
        """ ָ��SS�����临λ
        """
        debug_output('====\nCalib SS[%s]' % target_uid)
        acp_frame = [CV.ACP_FUNC_CODE_CALIB_PARA, ord('R'), SECURITY_CODE_HIGH8, SECURITY_CODE_LOW8]
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_DB, time_remains = 4, target_uid = target_uid)
        if ret:
            debug_output('SS Module[%s] calib reset' % target_uid)
        else:
            debug_output('SS Module[%s] reset failed' % target_uid)


    def fraz_ss_current_parameter_by_uid(self, target_uid, feature_code, parameter_code):
        """ ����uidѰַ������ģ�鵱ǰ����
        Params:
            target_uid: ģ��UId�� 'FFFFFFFFFFFF'Ϊͨ��UID��ַ
            feature_code: �������������룬Ϊ��ǰ����Ĳ���ֵ�Ժ��ȡʱ���ã�[0-255]
                            SS����ܱ���4�β���������Ϣ4�������������󣬺���Ķ�����Ϣ�Ḳ������Ĵ洢������Ϣ
            parameter_code: CV.PARA_VOLTAGE(��ѹ) | CV.PARA_CURRENT(����) | CV.PARA_TEMPERATURE(�¶�), ����"|"�����������
        Returns:
            ���ͨ�ųɹ�������feature_code
            ���ʧ�ܣ�����None
        """
        assert feature_code < 256, "feature code should be [0-255] integer"

        debug_output('====\nFreeze parameter of SS[%s], feature code %01X, para code %02X:' % (target_uid,feature_code,parameter_code))
        acp_frame = [CV.ACP_FUNC_CODE_FRAZ_PARA, ord('F'), feature_code, parameter_code]
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_DB, time_remains=5, target_uid = target_uid)
        print ret


    def read_ss_fraz_parameter_by_uid(self, target_uid, feature_code, parameter_code):
        """ ����uidѰַ����feature_codeΪ��������ȡģ���Ѷ������. ��ָ���Ĳ��������ڣ�������
        Params:
            target_uid: ģ��UId�� 'FFFFFFFFFFFF'Ϊͨ��UID��ַ
            feature_code: �������������룬[0-255]
                            SS����ܱ���4�β���������Ϣ4�������������󣬺���Ķ�����Ϣ�Ḳ������Ĵ洢������Ϣ
            parameter_code: CV.PARA_VOLTAGE(��ѹ) | CV.PARA_CURRENT(����) | CV.PARA_TEMPERATURE(�¶�), ����"|"�����������
        Returns:
            ���ͨ��ʧ�ܣ�����None
            ���ָ����ȡ�Ĳ��������ڣ�
            ����ɹ������ز�����Ϣ
        """
        assert feature_code < 256, "feature code should be [0-255] integer"
        debug_output('====\nRead parameter of SS[%s], feature code %01X, para code %02X:' % (target_uid, feature_code, parameter_code))
        acp_frame = [CV.ACP_FUNC_CODE_FRAZ_PARA, ord('R'), feature_code, parameter_code]
        ret = self.single_acp_transaction(acp_frame, ACP_IDTP_DB, time_remains=5, target_uid = target_uid)
        if ret:
            paras = [ret[2*i]*256+ret[2*i+1] for i in range(len(ret)/2)]
            paras = [item if item <32768 else item - 65536 for item in paras]

            debug_output('FRAZ PARAMETERS of SS[%s], FEATURE CODE %01X' % (uid, feature_code))
            i = 0
            if parameter_code & CV.PARA_TEMPERATURE:
                paras[i] = paras[i] * 1.0 / 100
                debug_output('TEMPERATURE:%.2f' % paras[i])
                i += 1

            if parameter_code & CV.PARA_CURRENT:
                paras[i] = paras[i] * 1.0 / 1000
                debug_output('CURRENT:%.2f' % paras[i])
                i += 1

            if parameter_code & CV.PARA_VOLTAGE:
                paras[i] = paras[i] * 1.0 / 100
                debug_output('VOLTAGE:%.2f' % paras[i])

            return tuple(paras)

        else:
            print 'uid [%s] read parameter fail' % target_uid

    def fraz_ss_current_parameter_by_broadcast(self, feature_code, parameter_code):
        """ �����㲥������ģ�鵱ǰ����
        Params:
            feature_code: �������������룬Ϊ��ǰ����Ĳ���ֵ�Ժ��ȡʱ���ã�[0-255]
                            SS����ܱ���4�β���������Ϣ4�������������󣬺���Ķ�����Ϣ�Ḳ������Ĵ洢������Ϣ
            parameter_code: CV.PARA_VOLTAGE(��ѹ) | CV.PARA_CURRENT(����) | CV.PARA_TEMPERATURE(�¶�), ����"|"�����������
        Returns:
            �㲥ʹ���޻ظ�ͨ�Ż��ƣ����ֻҪ����֡��CV�ɹ����������أ�tran_id����ʾ�ɹ�, ����ȷ������SS���յ�����˱����������ظ��㲥���
            ����ʧ�ܷ���None
        """

        assert feature_code < 256, "feature code should be [0-255] integer"

        debug_output('====\nBroadcast to freeze all SS'' present parameters, feature code %01X, para code %02X:' % (feature_code,parameter_code))
        acp_frame = [CV.ACP_FUNC_CODE_FRAZ_PARA, ord('F'), feature_code, parameter_code]
        ret = self.acp_send(acp_body = acp_frame, idtp =  ACP_IDTP_DB, req = 0, domain_id = [self.domain_id_high8, self.domain_id_low8])
        if ret is not None:
            time.sleep(1);      #TODO: �����֡����ʱ�����
        return ret





if '__main__' == __name__:
    cv = CV('com3')

    test_ss = ['570A004D0054','570A004F0026','5E1D0A098A71']
    # test_ss = ['5E1D0A098A71']

    try:
        # ret = interface.single_response_transaction('0000012342')
        # if ret is not None:
        #     print ret
        #
        # ret = interface.multiple_response_transaction('0000012342', timeout = 2)
        # print ret

        uid = cv.read_uid()
        print 'cv uid:', dec_array_to_asc_hex_str(uid)

        # result = interface.diag('ffffffffffff',0x41,0x10)
        # print result

        # cv.phy_send(range(20), xmode = 0x41, scan=1)
        # cv.dll_send('ffffffffffff', range(10))
        cv.powermesh.ebc_broadcast(xmode = 0x80, rmode= 0x80, scan = 1, window = 5)
        time.sleep(5)

        # cv.app_send(asc_hex_str_to_dec_array('112233445566'))
        # time.sleep(2)

        # print '********************************************\nset acp addr test'
        # set_vid = 0x6601
        # for uid in test_ss:
        #     cv.set_ss_acp_addr(uid,vid = set_vid,domain_id=cv.domain_id)
        #     set_vid = set_vid + 1
        #
        # print '********************************************\nread acp addr test'
        # for uid in test_ss:
        #     apdu = cv.inquire_ss_acp_addr(uid)
        #     if apdu:
        #         print dec_array_to_asc_hex_str(apdu)

        # print '********************************************\nread SS parameter by uid test'
        # for uid in test_ss:
        #     paras = cv.read_ss_current_parameter_by_uid(uid,CV.PARA_VOLTAGE|CV.PARA_CURRENT|CV.PARA_TEMPERATURE)
        #     if paras:
        #         print paras
        #
        # print '********************************************\nread SS parameter by vid test'
        # for i in range(1):
        #     paras = cv.read_ss_current_parameter_by_vid(0x6603,CV.PARA_VOLTAGE|CV.PARA_CURRENT|CV.PARA_TEMPERATURE)
        #     if paras:
        #         print paras
        #
        # print '********************************************\ncalib SS parameter test'
        # for uid in test_ss:
        #     try:
        #         result = cv.calib_ss_voltage_by_uid(uid,0,15)     #�����ƻ�SSԭ�е��Ѿ�У׼�Ĳ����� ���ֻ��index=0�ĵ�
        #         if result:
        #             print dec_array_to_asc_hex_str(result)
        #     except PvmException as pe:
        #         print str(pe)
        #
        #
        # print '********************************************\nsave and reset SS test'
        # for uid in test_ss:
        #     cv.save_ss_calib_by_uid(uid)
        # cv.reset_ss_by_uid('5E1D0A098A71')

        print '********************************************\nfraz SS params'

        # for uid in test_ss:
        #     result = cv.fraz_ss_current_parameter_by_uid(uid, 0x85, CV.PARA_TEMPERATURE)
        #     if result:
        #         print dec_array_to_asc_hex_str(result)
        result = cv.fraz_ss_current_parameter_by_broadcast(0x89, CV.PARA_TEMPERATURE|CV.PARA_VOLTAGE|CV.PARA_CURRENT)

        print '********************************************\nread fraz SS params'
        for uid in test_ss:
            result = cv.read_ss_fraz_parameter_by_uid(uid, 0x89, CV.PARA_TEMPERATURE|CV.PARA_VOLTAGE|CV.PARA_CURRENT)
            if result:
                print dec_array_to_asc_hex_str(result)



    finally:
        cv.close()
        del cv

        print "THE END"