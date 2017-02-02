# -*- coding: cp936 -*-

''' pyFlashProgrammer.py
    Author: Lv Haifeng
    Date: 2017-02-01
    Description: BL6810 Flash Programmer Control Program
'''

from serial import Serial, SerialException
import time
from pvm_util import *

DEBUG_ON = False

def readhexfile(filepath):

    data_buffer = [255]*32768
    data_chips = []

    with open(filepath,'r') as f:
        line_number = 0
        std_record_type = {'00','01','02','04'}

        for line in f:
            line_number += 1

            line = line[0:-1]           # last byte is /n
            record_start = line[0]
            record_len = line[1:3]
            record_addr = line[3:7]
            record_type = line[7:9]
            record_data = line[9:-2]
            record_checksum = line[-2:]

            # read & check
            assert (record_start == ':'),'line:%d: start flag error %s!' % (line_number, record_start)
            assert (record_type in std_record_type), 'line:%d: error record type %s!' % (line_number, record_type)
            assert (int(record_addr,16)+int(record_len,16) <= 32767), "line:%d: out of length range!" % line_number
            assert (int(record_len,16) == len(record_data)/2), "line:%d: indicated data length(%d) doesn''t match actual data length(%d)" % (line_number,int(record_len,16),len(record_data)/2)
            assert (sum(asc_hex_str_to_dec_array(line[1:])) % 256 == 0), "line:%d: crc check fail" % line_number

            # read until file over
            if record_type == '01':    # '01'���ݸ�ʽ��ʾ�ļ�����
                break

            #
            if record_type == '00':     # ��ȡ�ļ����ݴ����ڴ沢��¼���ݿ�����״̬
##                print("proc new line %d" % line_number)
                addr_start = int(record_addr,16)
                addr_end = int(record_addr,16)+int(record_len,16)
                data_buffer[addr_start:addr_end] = asc_hex_str_to_dec_array(record_data)

                for i in xrange(len(data_chips)):
##                    print("i:%d"%i)
                    if data_chips[i][0] <= addr_start < data_chips[i][1] \
                       or data_chips[i][0] < addr_end <= data_chips[i][1]:
                        raise AssertionError, "addr_start:%d,addr_end:%d is overlapped with existed block[%d,%d]" % (addr_start,addr_end,data_chips[i][0],data_chips[i][1]);
                    else:
                        if addr_start == data_chips[i][1]:
##                            print [data_chips[i][0],data_chips[i][1]]
                            data_chips[i][1] = addr_end
##                            print "->",[data_chips[i][0],data_chips[i][1]]
                            break
                        elif addr_end == data_chips[i][0]:
##                            print [data_chips[i][0],data_chips[i][1]]
                            data_chips[i][0] = addr_start
##                            print "->",[data_chips[i][0],data_chips[i][1]]
                            break
                else:
##                    print "add",[addr_start,addr_end]
                    data_chips.append([addr_start,addr_end]);

        # ����data_chips
##        print data_chips
        data_chips.sort()
##        print "after sort",data_chips
        for i in xrange(len(data_chips)):
            if DEBUG_ON:
                print i
            if i>0:
                while i < len(data_chips) and data_chips[i][0] == data_chips[i-1][1]:
                    if DEBUG_ON:
                        print "i=",i
                        print data_chips[i-1]
                    data_chips[i-1][1] = data_chips[i][1]
                    if DEBUG_ON:
                        print "=>",data_chips[i-1]
                    del data_chips[i]
                    if DEBUG_ON:
                        print "now:",data_chips
        return data_buffer,data_chips


# def uart_switch(ser, payload, timeout):
#     ''' Ӧ��ʽ����ͨ�ſ��ƣ���payload�·������ڣ����մ��ڵ������������ݲ�����
#     Input:
#         ser: �Ѵ򿪵�Serial����
#         payload���·��Ĵ������ݣ�str��ʽ
#         timeout�����ȴ�ʱ��
#     Return:
#         ���ڵ��������أ�str��ʽ
#         ��ʱ����None
#     '''
#     ser.write(payload)
#     time_start = time.clock()
#     rcv_data = None
#     rcv_bytes = 0
#     while time.clock() - time_start < timeout:
#         if ser.inWaiting() != rcv_bytes:
#             rcv_bytes = ser.inWaiting()
#             time.sleep(0.001)               # sleep 0.001�ֿ����ȶ�����֪��Ϊɶ, �ڹ��ػ����Ƿ�һ���д�����
#         else:
#             if rcv_bytes >0 :
#                 rcv_data = ser.read(rcv_bytes)
#                 break
#     else:               #time out occured
#         pass
#     return rcv_data

def uart_switch(ser, payload, timeout):
    ''' Ӧ��ʽ����ͨ�ſ��ƣ���payload�·������ڣ����մ��ڵ������������ݲ�����
        ����֡��ʽ�ĳ�����Ϣ
    Input:
        ser: �Ѵ򿪵�Serial����
        payload���·��Ĵ������ݣ�str��ʽ
        timeout�����ȴ�ʱ��
    Return:
        ���ڵ��������أ�str��ʽ
        ��ʱ����None
    '''
    ser.write(payload)
    time_start = time.clock()
    rcv_data = None
    frm_len = 9999
    while time.clock() - time_start < timeout:
        if ser.inWaiting() + 3 >= frm_len:
            rcv_data += ser.read(ser.inWaiting())
            break
        elif ser.inWaiting() >= 3:
            rcv_data = ser.read(3)
            frm_len = ord(rcv_data[1])*256 + ord(rcv_data[2])
    else:               #time out occured
        pass
    return rcv_data

class FlashProgrammerException(Exception):
    ''' Flash Programmer���ص��쳣����ϸ��Ϣͨ��raiseʱЯ�����ַ�������
    '''
    pass


class FlashProgrammer(object):
    def __init__(self, port):
        self.ser = Serial(port, baudrate = 115200, bytesize=8, parity='N', stopbits=1)
        self.port = port
        self.max_payload_length = 256   # ÿ����ഫ���ֽ���
        self.passwd = '9527'
        self.timeout = 1                # �������ʱʱ��
        self.max_retry = 1              # ������Դ���

        self.read_prog_type()           # ������ͨ��

    def gen_command_frame(self, command, body = [], bring_passwd = False):
        ''' ���ɱ������������
            ����������ʽ��
            ������1B	���ݰ�����2B	����NB	��ȫ������4B	CRCУ��2B
            �ο�<2011-08-25 PLC1G�������������ƽӿڶ���v1.2.docx>
        Input:
            command: ������, dec byte
                ����	������
                ��������ͺŰ汾�Ŷ�ȡ	0x10
                Ŀ��Ӳ�����Ͷ�ȡ	0x11
                ȫоƬ����*	0x20
                ȫMainArray����*	0x21
                ȫ�û�����������	0x22
                ȫNVR����	0x23
                ȫMainArray�ֽڱ��*	0x30
                �û�������ָ���ֽڱ��	0x31
                NVR�ֽڱ��	0x32
                ȫоƬ���ݶ�ȡ*	0x40
                �û����������ݶ�ȡ	0x41
                NVR�ֽڶ�ȡ	0x42
                �û�����������	0x50
                �������������(TBD)	0x51
                Ŀ��������λ	0x80
            body: ���壬dec byte array
        Return:
            ����֡��dec byte array
        '''
        if bring_passwd:
            frm_len = len(body) + 9
        else:
            frm_len = len(body) + 5

        frm = [command, int(frm_len/256), frm_len % 256] + body
        if bring_passwd:
            frm += [ord(c) for c in self.passwd]
        frm += crc16(frm)
        return frm

    def command_transaction(self, command):
        ''' �����������
        Input��
            command: dec array����������
        Return:
            ��д��ִ�гɹ������ش�������
            ִ��ʧ�ܣ�����Exception
        '''
        str_command = [chr(n) for n in command]
        ret = None

        for i in range(self.max_retry + 1):
            ret = uart_switch(self.ser, str_command, self.timeout)
            if ret:
                ret = [ord(c) for c in ret]
                if [0xE2, 0xF0] == crc16(ret):
                    if ret[0] != 0x80:
                        if ret[3] != 0x10:      #�������ʾ����CRC���������ԣ�������raise Exception
                            print u'����������쳣,����0x%02X' % ret[3]
                            raise FlashProgrammerException('Programmer Error Code 0x%02X' % ret[3])
                    else:
                        return ret[3:-2]
            else:
                pass    #���������CRCʧ�ܣ�����
        else:
            if ret is None:
                print u'���������Ӧ,���(1)������Ƿ��ϵ�? (2)�����Ƿ�Ͽ�? (3)������Ƿ���ȷ?'
                raise FlashProgrammerException('Programmer No Response')
            elif [0xE2, 0xF0] != crc16(ret):
                print u'�������������CRCУ��ʧ��, ��飨1������������2��������Ƿ���ȷ'
                raise FlashProgrammerException('Uplink CRC Fail')
            elif ret[0] == 0xF0 and ret[3] == 0x10:
                print u'�������ʾ����CRCУ��ʧ��, ��������Ƿ�Ӵ�����'
                raise FlashProgrammerException('Downlink CRC Fail')
            else:
                print u'δ֪����ret:%s' % dec_array_to_asc_hex_str(ret)
                raise FlashProgrammerException('Unknown Error')


    def read_prog_type(self):
        ''' ��������ͺ�
            �����ֽ�[��������ͣ��̼��汾��FIRM_MAJOR_VERSION�� FIRM_MINOR_VERSION�� VER_YEAR�� VER_MONTH�� VER_DAY]
        '''
        ret = self.command_transaction(self.gen_command_frame(0x10))
        if ret[0] == 0x01:
            prog_type = 'SystemLoader'
        elif ret[1] == 0x02:
            prog_type = 'OnlineLoader'
        else:
            prog_type = 'Unknown'
        print '%s connected on %s' % (prog_type, self.port)

    def read_nvr(self, nvr_addr, read_len):
        ''' ��оƬ��nvr��, �����������ʽ[1B���� NB������]
        Input:
            nvr_addr: nvr��ʼ��ַ��ʮ������������ e.g. 0x0010
            read_len: ���ֽ���. e.g. 10
        Return��
            ��ȡ��nvr��Ϣ��dec array
        '''
        return self.command_transaction(self.gen_command_frame(0x42, [int(nvr_addr/256), nvr_addr%256, read_len]))[1:]


    def read_uid(self):
        ''' ��оƬuid������ʮ�������ַ���
            BL6810 UID�洢��NVR��ַ0x300~0x305��ַ
        '''
        return dec_array_to_asc_hex_str(self.read_nvr(0x300,6))


    def erase_full_main_array(self):
        ''' ��������main array
        '''
        self.command_transaction(self.gen_command_frame(0x21, bring_passwd = True))
        print 'Target Chip Main Array Erased'


    def reset_target(self):
        ''' ����Ŀ��оƬ
        '''
        self.command_transaction(self.gen_command_frame(0x80, bring_passwd = True))
        print 'Target Chip Reset'


    def full_main_array_burn(self, hex_file_path):
        ''' ��������main array�󣬽�hex�ļ���¼
            ��¼������д����֤
        '''

        start_time = time.clock()

        self.erase_full_main_array()
        time.sleep(0.1)                # �ȴ��������

        data_buffer, data_chips = readhexfile(hex_file_path)
        for [start, end] in data_chips:
            while start < end:
                if end - start < self.max_payload_length:
                    payload = data_buffer[start:end]
                else:
                    payload = data_buffer[start: (start + self.max_payload_length)]
                self.command_transaction(self.gen_command_frame(0x30, [int(start/256), start % 256, len(payload)%256] + payload, bring_passwd = True))
                start = (start + self.max_payload_length)

        self.reset_target()
        print 'Main Array Burned, Cost %.2fs' % (time.clock()-start_time)


if '__main__' == __name__:
    prog = FlashProgrammer('com8')
    try:
        # prog.burn(r'e:\unify_root\project\pv_mon\firmware\powermesh_unify_2.0\device_ss\mainstream\project\powermesh_ss.hex')
        # prog.erase_full_main_array()
        # print dec_array_to_asc_hex_str(prog.gen_command_frame(0x21,bring_passwd=1))
        # print dec_array_to_asc_hex_str(prog.read_nvr(0,64))
        # prog.reset_target()
        prog.full_main_array_burn(r'e:\unify_root\project\pv_mon\firmware\powermesh_unify_2.0\device_ss\mainstream\project\powermesh_ss_ifp.hex')
        # prog.full_main_array_burn(r'E:\Users\Mac\Documents\My Sync\Python\mac_python\project\ifp\qc.hex')
    except FlashProgrammerException as e:
        print 'Exception:', type(e),str(e)
    finally:
        prog.ser.close()
