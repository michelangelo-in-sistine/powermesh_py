#!d:\\python27 python2.7
# -*- coding: cp936 -*-

import powermesh_rscodec

POWERMESH_INNER_DATA_TYPE = list                  # in release version, inner data type should be bytearray
PRINT_DEBUG_INFO = True


def asc_hex_str_to_dec_array(asc_hex_str):
    asc_hex_str = ''.join([c for c in asc_hex_str if c != ' '])      # get rid of blank character
    assert (len(asc_hex_str) % 2 == 0), 'input length error: %s' % (asc_hex_str,)
    temp = [int(asc_hex_str[i:i+2],16) for i in xrange(len(asc_hex_str)) if i % 2 == 0]
    return POWERMESH_INNER_DATA_TYPE(temp)


def dec_array_to_asc_hex_str(dec_list, seperator = ''):
    temp = ['%02X' % n for n in dec_list]
    return seperator.join(temp)

def debug_output(s):
    if PRINT_DEBUG_INFO:
        print(s)


def crc16(data):
    """
    Params:
        data: input dec list
    Return:
        dec list for calce
    """
    assert(type(data)==POWERMESH_INNER_DATA_TYPE), 'input data must be a %s' % (POWERMESH_INNER_DATA_TYPE,)

    crc = 0xFFFF
    for newbyte in data:
        for j in xrange(8):
            crcbit = 1 if (crc & 0x8000) else 0
            databit = 1 if (newbyte & 0x80) else 0
            crc = (crc<<1) % 0x10000
            if crcbit != databit:
                crc ^= 0x1021
            newbyte = (newbyte<<1) % 0x100
    crc ^= 0xFFFF

    return POWERMESH_INNER_DATA_TYPE([crc>>8, crc%256])

def check_bit(value, bit):
    # 判断value的第bit位是否为1
    if value & 0x01<<bit:
        return True
    else:
        return False


def calc_cs(data):
    """ 计算list的校验码
        该校验码应使得原数据的求和与校验之和能被256整除
    """
    if type(data) == int:
        return -data % 256
    else:
        return -sum(data) % 256



def parse(phy_data, encode='asc_hex'):
    # 解析powermesh物理层数据包
    if phy_data != '' and encode == 'asc_hex':
        phy_data = POWERMESH_INNER_DATA_TYPE(asc_hex_str_to_dec_array(phy_data))

    if len(phy_data) < 4:
        print u'错误的数据包长度, 应至少4字节'

    print("================================\nPHY Layer:")
    if len(phy_data) == 4:
        # SRF数据包
        cs = (256 - (sum(phy_data[:-1]) % 256)) % 256
        disturb = (phy_data[-1] - cs) % 256
        first_byte = phy_data[0]

        print u"可能为SRF数据包, 扰码%02X" % (disturb)

        if check_bit(first_byte,7):
            print u'ESF数据包'
            print phy_data
            print u'NAV值0x%04X' % (phy_data[1] * 256 + phy_data[2])
            return
        elif check_bit(first_byte,2):
            print(u'SRF数据包, 应该是EBC的SBRF响应帧')
            if check_bit(first_byte,3):
                print(u'SCAN类型, 版本号0x%02X' % (first_byte % 4))
            else:
                print(u'非scan类型, 版本号0x%02X' % (first_byte % 4))
        else:
            print(u'符合SRF数据包特征,但没有标志位')
            return


        #  check freq
        a = first_byte>>4
        if (a % 8) >= 4:
            print(u'频率通道:四通道')
        else:
            print(u'频率通道:CH%02X' % (a % 8))

        print(u'广播ID:0x%02X' % (phy_data[1]>>4))
        print(u'随机ID:0x%04X' % ((phy_data[1] % 16)*256 + phy_data[2]))
    else:
        #普通数据包
        ## PHY 解析
        cs = (256 - (sum(phy_data[0:9]) % 256)) % 256
        disturb = (phy_data[9] - cs) % 256
        first_byte = phy_data[0]

        if crc16(phy_data[:-1]+[phy_data[-1]^disturb]) != [0xE2, 0xF0]:
            phy_data = powermesh_rscodec.rsdecode_vec(phy_data)
            if crc16(phy_data[:-1]+[phy_data[-1]^disturb]) == [0xE2, 0xF0]:
                datarate = 0
                print(u"RS解码后校验通过! BPSK类型, 扰码0x%02X" % disturb)
            else:
                print(u"crc 校验错误")
                return
        else:
            datarate = 1
            print(u'crc校验通过!扰码0x%02X,无RS编码' % disturb)

        ## check scan
        if check_bit(first_byte, 3):
            scan = 1
            print(u'SCAN, 版本号0x%02X' % (first_byte % 4))
        else:
            scan = 0
            print(u'非SCAN, 版本号0x%02X' % (first_byte % 4))

        ## check srf
        if check_bit(first_byte,  2):
            print(u'出现了SRF标志,错误!')
            return

        ## check freq
        a = int(first_byte/16)
        if a >= 8:
            print(u'物理层长包类型')
        if (a % 8) >= 4:
            print(u'频率通道:四通道')
        else:
            print(u'频率通道:CH%d' % (a % 8))

        if datarate == 0:
            print(u'速率: 有RS编码, 可能是BPSK')
        else:
            print(u'速率: 无RS编码, 可能是DS15或DS63')
        print(u'物理层长度:%d Bytes' % len(phy_data))


        ## DLL解析
        print('--------\nDLL Layer:')
        ind_len = int(first_byte/128)*256 + phy_data[1]
        if ind_len != len(phy_data):
            print(u'长度信息不符')
            return
        if (sum(phy_data[:10])-disturb) % 256 != 0:
            print(u'CS校验不符')
            return

        print(u'目的地址UID:%02X%02X%02X%02X%02X%02X' % (phy_data[3], phy_data[4], phy_data[5], phy_data[6], phy_data[7], phy_data[8]))
        print(u'源地址UID:%02X%02X%02X%02X%02X%02X' % (phy_data[10], phy_data[11], phy_data[12], phy_data[13], phy_data[14], phy_data[15]))
        dlct = phy_data[9]

        if check_bit(dlct, 7):
            if (dlct % 64)>>2 == 15:
                print(u'DLL协议:扩展DLL协议(EDP)')
                lsdu = phy_data[16:-2]
                if lsdu[0] >> 6 == 1:
                    print(u'协议:EBC\n帧类型')
                    if lsdu[0] % 4 == 0:
                        print(u'EBC广播帧(NBF)')
                        print(u'要求返回类型:0x%s' % response_mode(lsdu[0],scan))
                        print(u'广播ID:0x%02X' % (lsdu[1]>>4))
                        print(u'窗口数:%d' % 2**(lsdu[1]%16))
                        print(u'响应MASK:%8s (X X BUILD_ID METER_ID UID SNR SS AC_PHASE)' % bin(lsdu[2])[2:])
                        print(u'响应条件: %s' % dec_array_to_asc_hex_str(lsdu[3:], ' '))
                    elif lsdu[0] % 4 == 1:
                        print(u'EBC随机ID查询帧(NIF)')
                        print(u'要求返回类型:0x%s' % response_mode(lsdu[0],scan))
                        print(u'广播ID:0x%02X' % (lsdu[1]>>4))
                        print(u'随机ID:0x%04X' % ((lsdu[1] % 16)*256 + lsdu[2]))
                    elif lsdu[0] % 4 == 2:
                        print(u'EBC随机ID响应帧(NAF)')
                        print(u'广播ID:0x%02X' % (lsdu[1] >> 4))
                        print(u'随机ID:0x%04X' % ((lsdu[1] % 16)*256 + lsdu[2]))
                    elif lsdu[0] % 4 == 3:
                        print(u'EBC确认帧(NCF)')
                        print(u'广播ID:0x%02X' % (lsdu[1]>>4))
                        print(u'随机ID:0x%04X' % ((lsdu[1] % 16)*256 + lsdu[2]))
                    else:
                        print(u'不能识别的EDP/EBC数据帧')
                else:
                    print(u'不支持的EDP协议')
                return

            else:
                print(u'Diag类型')
                if not check_bit(dlct, 6):
                    print(u'下行')
                    print(u'要求返回类型:0x%s' % response_mode(dlct,scan))
                else:
                    print(u'响应')
                    print(u'LSDU:'),
                    print(phy_data[16:-2])
                print(u'序列号:%d' % (dlct % 4))
                return
        else:
            print(u'普通类型')
            if not check_bit(dlct, 6):
                print(u'下行')
                if check_bit(dlct, 5):
                    print(u'要求响应')
                else:
                    print(u'不要求响应')
            else:
                print(u'响应包')
            print(u'序列号:%d' % (dlct % 4))
        print('LSDU:'),
        print(phy_data[16:-2])

        ##Network测试
        lsdu = phy_data[16:-2]
        if not len(lsdu)==0:
            print(u'--------\nNW Layer:')
            if lsdu[0] >> 4 == 6:
                print(u'网络层协议:PSR')
                print(u'PIPE_ID:0x%04X' % ((lsdu[0] % 16)*256+lsdu[1]))
                print(u'PIPE_INDEX:0x%02X' % (lsdu[2] % 4))

                if check_bit(lsdu[2],5):
                    print(u'PIPE_TYPE:Bi-way pipe')
                else:
                    print(u'PIPE_TYPE:Single-way pipe')


                if check_bit(lsdu[2],3):
                    print(u'Direction:Uplink')
                else:
                    print(u'Direction:Downlink')

                if check_bit(lsdu[2],2):
                    print(u'Error Feedback')
                    print(u'Error Uid:%s' % dec_array_to_asc_hex_str(lsdu[3:9]))
                    print(u'Error Code:0x%02X:' % lsdu[9])
                    if lsdu[9] == 0:
                        print(u'No Error.')
                    elif lsdu[9] == 1:
                        print(u'No Pipe Info.')
                    elif lsdu[9] == 2:
                        print(u'No Xmt Plan.')
                    elif lsdu[9] == 3:
                        print(u'Ack Time Out.')
                    elif lsdu[9] == 4:
                        print(u'Mem Out.')
                    else:
                        print(u'Unknow Err Code.')

                print(u'PIPE_INDEX:0x%02X' % (lsdu[2]%4))
                if check_bit(lsdu[2],7):
                    print(u'Packet Type: Setup Package')
                elif check_bit(lsdu[2],6):
                    print(u'Packet Type: Patrol Package')
                else:
                    print(u'Packet Type: Transmit Package')
                print(u'NSDU(%d bytes:%s' % (len(lsdu[3:]), dec_array_to_asc_hex_str(lsdu[3:])))

            elif lsdu[0] >> 4 == 1:
                print(u'网络层协议:DST')
                if len(lsdu)<7:
                    print(u'LSDU数据长度错误%d' % len(lsdu))

                conf = lsdu[0]
                jumps = lsdu[1]
                forward = lsdu[2]

                print(u'flood id:0x%02X' % (conf % 4))
                if check_bit(conf,3):
                    print(u'Flooding Search,')
                else:
                    print(u'Flooding transmit,')

                if check_bit(conf,2):
                    print(u'上行')
                else:
                    print(u'下行')

                print(u'总跳数:%d,剩余跳数%d' % (jumps>>4, jumps%16))

                if check_bit(forward,4):        #check acps_ena
                    print(u'相位约束,转发携带ACPS:0x%02X' % lsdu[3])

                if check_bit(forward,5):        #check network_id_ena
                    print(u'网络约束,转发携带网络ID:0x%02X' % lsdu[4])

                if forward % 8:
                    print(u'第%d跳,转发窗口数:%d,所在窗口序列号:%d' % int(jumps/16) - mod(jumps % 16), 2**(forward % 8), lsdu[5])

                if check_bit(forward,3):
                    print(u'转发窗口递减使能')

                print(u'NSDU(%d bytes):%s' % (len(lsdu[6:]), dec_array_to_asc_hex_str(lsdu[6:])))

            elif (lsdu[0] >> 4)==15:
                print(u'网络层协议:PTP')
                print(u'NSDU(%d bytes):%s' % (len(lsdu[1:]), dec_array_to_asc_hex_str(lsdu[1:])))
            else:
                print(u'无法识别的网络层协议')