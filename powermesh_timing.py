#!/usr/bin/env python2.7
# -*- coding:utf8 -*-

import powermesh_spec

class PowermeshTiming():
    def __init__(self):
        self.bpsk_bit_timing = 24*38/5e6            # 有5e6默认按浮点数处理
        self.ds15_bit_timing = 24*38/5e6*15
        self.ds63_bit_timing = 24*38/5e6*63
        
        self.bpsk_bit_rate = 5e6/(24*38)
        self.ds15_bit_rate = 5e6/(24*38)/15
        self.ds63_bit_rate = 5e6/(24*38)/63
        
        self.phy_framing_cost = 24+11+22            # 物理层同步头,同步码,EOP开销
        self.scan_interval = 0.010                  # scan包之间间隔

        self.ACK_DELAY_STICKS = 0.025
        self.DLL_SEND_DELAY_STICKS = 0.025
        self.SOFTWARE_DELAY_STICKS = 0.005
        self.HARDWARE_DELAY_STICKS = 0.005

        self.RCV_SCAN_MARGIN_STICKS = 0.02
        self.RCV_SINGLE_MARGIN_STICKS = 0.002
        self.RCV_RESP_MARGIN_STICKS = 0.1
        self.EBC_WINDOW_MARGIN_STICKS = 0.010

        self.PSR_STAGE_DELAY_STICKS = self.DLL_SEND_DELAY_STICKS + 0.015
        self.PSR_MARGIN_STICKS = 1

        self.CV_MARGIN_STICKS = 0.5
        self.PTP_MARGIN_STICKS = 1
    
    def basic_bit_timing(self, rate):
        if rate == 'bpsk' or rate == 0:
            return self.bpsk_bit_timing
        elif rate == 'ds15' or rate == 1:
            return self.ds15_bit_timing
        elif rate == 'ds63' or rate == 2:
            return self.ds63_bit_timing
        else:
            raise ValueError('Error rate %s' % rate)
    
    def phy_basic_bit_rate(self, rate):
        if rate == 'bpsk' or rate == 0:
            return self.bpsk_bit_rate
        elif rate == 'ds15' or rate == 1:
            return self.ds15_bit_rate
        elif rate == 'ds63' or rate == 2:
            return self.ds63_bit_rate
        else:
            raise ValueError('Error rate %s' % rate)

    def phy_packet_bits(self, phy_bytes):
            return self.phy_framing_cost + phy_bytes * 11

    def phy_packet_timing(self, phy_bytes, rate='bpsk', scan=False):
        timing = self.phy_packet_bits(phy_bytes) * self.basic_bit_timing(rate)
        if scan:
            timing = timing * 4 + self.scan_interval * 3    # scan数据包重复4遍
        return timing

    def phy_srf_packet_timing(self, rate='bpsk', scan=False):
        return self.phy_packet_timing(4, rate, scan)                # 基本srf 4字节
        
    def app_psr_packet_timing(self, apdu_bytes, rate):
        return self.phy_packet_timing(apdu_bytes + 18 + 3 + 1)
    
    def app_dst_packet_timing(self, apdu_bytes, rate, scan):
        return self.phy_packet_timing(apdu_bytes + 18 + 6 + 1, rate, scan)

    def dll_send_timing(self, lsdu_len, rate, scan, delay):
        return self.phy_packet_timing(lsdu_len + powermesh_spec.LEN_TOTAL_OVERHEAD_BEYOND_LSDU, rate, scan) + delay

    def dll_ack_expiring_timing(self, ppdu_len, rate, scan):
        timing = self.phy_packet_timing(ppdu_len, rate, scan)
        if scan:
            timing += 2 * self.RCV_SCAN_MARGIN_STICKS
        timing += self.ACK_DELAY_STICKS + self.SOFTWARE_DELAY_STICKS + self.HARDWARE_DELAY_STICKS + self.RCV_RESP_MARGIN_STICKS
        return timing + self.CV_MARGIN_STICKS

    def windows_delay_timing(self, phy_bytes, rate, scan, window):
        timing = self.phy_packet_timing(phy_bytes, rate, scan)
        timing += self.EBC_WINDOW_MARGIN_STICKS
        timing = timing * 2**window + self.ACK_DELAY_STICKS + self.RCV_SCAN_MARGIN_STICKS + self.CV_MARGIN_STICKS
        return timing

    def flooding_transaction_timing(self, down_apdu_bytes, up_apdu_bytes, rate, scan, jumps, windows, resp_delay=1):
        sticks = self.app_dst_packet_timing(down_apdu_bytes, rate, scan)
        total_sticks = sticks

        sticks = self.windows_delay_timing(down_apdu_bytes + 18 + 6 + 1, rate, scan, windows)
        total_sticks += sticks * jumps

        sticks = self.app_dst_packet_timing(up_apdu_bytes, rate, scan)     # 始发的上行帧
        total_sticks += sticks

        sticks = self.windows_delay_timing(up_apdu_bytes + 18 + 6 + 1, rate, scan, windows)
        total_sticks += sticks * jumps

        return total_sticks + self.PSR_MARGIN_STICKS + resp_delay

    def psr_setup_transaction_timing(self, pipe_script):
        """ pipe_script必须是已经去除了空格的pipe描述字符串
            与C语言版本的差异: C语言版本不包括psr第一次发送的时间(因为从发送完毕开始计时), python版本包括这个时间
        """
        assert len(pipe_script) >= 16 and len(pipe_script) % 16 == 0, 'pipe_script error: %s' % pipe_script
        stages = len(pipe_script)/16
        timing = 0
        pack_len = 18+3+1+7*(stages-1)
        resp_len = powermesh_spec.LEN_TOTAL_OVERHEAD_BEYOND_LSDU + 3

        # 下行总时间
        for i in xrange(stages):
            xmode = int(pipe_script[i*16+12:i*16+14],16)
            pack_timing = self.phy_packet_timing(pack_len, xmode % 4 ,0)
            timing += pack_timing + self.SOFTWARE_DELAY_STICKS + self.HARDWARE_DELAY_STICKS + self.ACK_DELAY_STICKS + self.PSR_STAGE_DELAY_STICKS
            pack_len -= 7   # 下行包每次递减7字节

        # 上行总时间
        for i in xrange(stages):
            rmode = int(pipe_script[i*16+14:i*16+16],16)
            pack_timing = self.phy_packet_timing(resp_len, rmode % 4 ,0)
            timing += pack_timing + self.SOFTWARE_DELAY_STICKS + self.HARDWARE_DELAY_STICKS + self.ACK_DELAY_STICKS + self.PSR_STAGE_DELAY_STICKS

        return timing + self.PSR_MARGIN_STICKS


    def ptp_single_acp_transaction_timing(self, acp_frame_bytes, expect_acp_return_bytes, xmode = 0x80):
        """ 网络层选择ptp协议
        """
        down_timing = self.phy_packet_timing(acp_frame_bytes + powermesh_spec.SEC_ACP_VC_BODY + powermesh_spec.LEN_TOTAL_OVERHEAD_BEYOND_LSDU + powermesh_spec.LEN_PTP_NPCI + powermesh_spec.LEN_MPCI, xmode & 0x03)
        up_timing = self.phy_packet_timing(expect_acp_return_bytes + powermesh_spec.SEC_ACP_VC_BODY + powermesh_spec.LEN_TOTAL_OVERHEAD_BEYOND_LSDU + powermesh_spec.LEN_PTP_NPCI + powermesh_spec.LEN_MPCI, xmode & 0x03)
        return down_timing + up_timing + self.PTP_MARGIN_STICKS

if __name__=='__main__':
    tim = PowermeshTiming()

    print tim.bpsk_bit_timing
    print tim.ds15_bit_timing
    print tim.ds63_bit_timing

    print tim.bpsk_bit_rate
    print tim.ds15_bit_rate
    print tim.ds63_bit_rate
    
    print tim.phy_packet_bits(11)
    print 'srf timing:', tim.phy_srf_packet_timing(rate=0, scan=True)
    print 'app psr timing:', tim.app_dst_packet_timing(40, rate=2, scan=True)

    print 'flooding:', tim.windows_delay_timing(52+18+6+1,1,1,16)
    print 'flooding transaction:', tim.flooding_transaction_timing(52,52,'bpsk',scan = True,jumps=1,windows=16,resp_delay=1)
    
    print 'Timing Test Exit'

    print tim.psr_setup_transaction_timing('5e1d0308775220405e1d040877398020')
