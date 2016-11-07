#!d:\\python27 python2.7
# -*- coding: cp936 -*-
# author: Lv Haifeng
# ver: 1.0
# 2016-10-18

from serial import Serial, SerialException
from threading import Thread
import time
from pvm_util import *
from Queue import Queue
import re
import pvm_protocol


class Interface(object):
    """\
    Create a layer object between CV device and transaction entity
    """

    def __init__(self, port, baudrate = 115200):
        self.init = False
        self.port_on = False
        try:
            self.ser = Serial(port, baudrate = baudrate, bytesize=8, parity='N', stopbits=1)
            self.com = port
            self.baudrate = baudrate
            debug_output('%s open successfully' % self.com)
            self.port_on = True

            ## �����߳�����
            self.start_rcv_loop_thread()

            self.queue = Queue()
            self.init = True
        except SerialException:
            debug_output("%s open fail!" % port)


    def __del__(self):
        '''
            __del__()ֻ���������ڲ���Ա��û�б����õ�ʱ��ű����ã����������˵������ser�رգ�rcv_loop�˳�
            ���__del__()������������ʵ���õ�quit_rcv_loop_thread()��ser.close()�������õ�
            ��Ϊ�������������������Ļ���__del__()�����������ᱻִ��

            �������ĵ���Ҫ�����㣺1��uart io�ڱ�ռ���޷��ٴδ� 2��������rcv_loop_thread()�̲߳��ܽ���������ѭ��
            ʵ��֤ʵ��������������µ���python xxx.pyִ�е�python����
            ���������������python����ǿ�йر�
            ��Ȼ�������__del__()����
            ��uart io��رգ�rcv_loop_thread�����߳�Ҳ�ᱻ����

            �������赣��
        '''
        debug_output("eliminate Interface object")
        try:
            self.quit_rcv_loop_thread()         # �����߳̽���
            self.ser.close()
        except Exception as e:
            debug_output("except happened when Interface object destructed!")
            print e


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


    def write(self, write_str):
        self.ser.write(write_str)


    def send(self, decimal_array):
        # data: a list of DECIMAL BYTE DATA
        # output: '<ASC_HEX_STR>'
        if self.port_on:
            self.ser.write('<' + dec_array_to_asc_hex_str(decimal_array) + '>')
        else:
            print('port is not opened')


    def rcv_loop(self):
        ## ����CV�����ı��Ķ����߳�
        ## �з���CVͨ��Э��������������Queue��

        self.rcv_loop_thread_on = True

        rcv_data = ''
        rcv_bytes = 0
        while self.rcv_loop_thread_on:
            debug_output('loop')
            try:
                if self.ser.inWaiting() != rcv_bytes:
                    rcv_bytes = self.ser.inWaiting()        # receving status
                else:
                    if rcv_bytes:
                        rcv_data += self.ser.read(rcv_bytes) # ����ȡ����״̬����
                        rcv_bytes = 0

                        # �����Ч�Ľ��ղ��������Queue��
                        match_rslt = re.findall(r'<(\w+)>',rcv_data)
                        if match_rslt:
                            for item in match_rslt:
                                self.queue.put(item)
                            index = rcv_data.rfind(match_rslt[-1]) + len(match_rslt[-1]) + 1    #
                            rcv_data = rcv_data[index:]
                time.sleep(0.001)
            except SerialException:
                debug_output('Comm Object is Cleared')
                self.rcv_loop_thread_on = False
                self.queue.put(None)
                break;
        debug_output('rcv loop thread quit')


    def start_rcv_loop_thread(self):
        self.rcv_loop_thread = Thread(target = self.rcv_loop)
        self.rcv_loop_thread.start()


    def quit_rcv_loop_thread(self):
        self.rcv_loop_thread_on = False

    def get_queue(self):
        ## get handle of queue
        return self.queue


if '__main__' == __name__:
    interface = Interface('com4')
    a = asc_hex_str_to_dec_array('123456')
    # 5/0

    a = ''
    while a != 'quit':
        a = raw_input('>')
        interface.write(a)
    else:
        interface.turn_off()
    print "THE END"