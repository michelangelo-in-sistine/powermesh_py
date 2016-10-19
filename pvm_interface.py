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


class Interface(Serial):
    """\
    Create a layer object between CV device and transaction entity

    """

    def __init__(self, port):
        self.com = port
        self.init = False
        self.port_on = False
        try:
            Serial.__init__(self, port, baudrate=115200, bytesize=8, parity='N', stopbits=1)
            self.com = port
            debug_output('%s open successfully' % self.com)
            self.port_on = True

            ## �����߳�����
            self.rcv_loop_thread = Thread(target = self.rcv_loop)
            self.rcv_loop_thread_on = True
            self.rcv_loop_thread.start()
            self.rcv_loop_thread.join()

            self.init = True
            self.queue = Queue()
        except SerialException:
            print "%s open fail!" % port

    def turn_on(self):
        # �����븸��open()��������, ��Ϊ����open()������__init__()�б�����, �����䷽���ᵼ�¸����ʼ������

        if not self.port_on:
            self.__init__(self.com)

    def turn_off(self):
        self.rcv_loop_thread_on = False     # �����߳̽���
        self.close()
        self.port_on = False


    def send(self, decimal_array):
        # data: a list of DECIMAL BYTE DATA
        # output: '<ASC_HEX_STR>'
        if self.port_on:
            Serial.write(self, '<' + dec_array_to_asc_hex_str(decimal_array) + '>')
        else:
            print('port is not opened')


    def rcv_loop(self):
        ## ����CV�����ı��Ķ����߳�
        ## �з���CVͨ��Э��������������Queue��

        rcv_bytes = 0
        while self.rcv_loop_thread_on:
            time.sleep(0.2)
            if self.inWaiting() != rcv_bytes:
                rcv_bytes = self.inWaiting()        # receving status
            else:
                if rcv_bytes:
                    rcv_data = self.read(rcv_bytes) # ����ȡ����״̬����
                    rcv_bytes = 0

                    debug_output(rcv_data)

                    # �����Ч�Ľ��ղ��������Queue��
                    match_rslt = re.findall(r'<(\w+)>',rcv_data)
                    if match_rslt:
                        for item in match_rslt:
                            self.queue.put(item)

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