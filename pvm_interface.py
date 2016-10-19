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

            ## 接收线程启动
            self.rcv_loop_thread = Thread(target = self.rcv_loop)
            self.rcv_loop_thread_on = True
            self.rcv_loop_thread.start()
            self.rcv_loop_thread.join()

            self.init = True
            self.queue = Queue()
        except SerialException:
            print "%s open fail!" % port

    def turn_on(self):
        # 避免与父类open()方法重名, 因为父类open()方法在__init__()中被调用, 覆盖其方法会导致父类初始化出错

        if not self.port_on:
            self.__init__(self.com)

    def turn_off(self):
        self.rcv_loop_thread_on = False     # 接收线程结束
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
        ## 监视CV返回文本的独立线程
        ## 有符合CV通信协议的数据则将其放入Queue中

        rcv_bytes = 0
        while self.rcv_loop_thread_on:
            time.sleep(0.2)
            if self.inWaiting() != rcv_bytes:
                rcv_bytes = self.inWaiting()        # receving status
            else:
                if rcv_bytes:
                    rcv_data = self.read(rcv_bytes) # 整包取出并状态清零
                    rcv_bytes = 0

                    debug_output(rcv_data)

                    # 获得有效的接收并将其放入Queue中
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