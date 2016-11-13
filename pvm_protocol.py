#!d:\\python27 python2.7
# -*- coding: cp936 -*-

import powermesh_rscodec
from pvm_util import *


def response_mode(dlct,scan):
    rmode = (dlct % 64) >> 2
    if scan:
        if rmode==0x0C:
            type = '0C:scan+bpsk'
        elif rmode==0x0D:
            type = '0D:scan+ds15'
        elif rmode==0x0E:
            type = '0E:scan+ds63'
        else:
            type = 'ERROR DISP Mode!!'
    else:
        if rmode == 0x00:
            type = '10:CH0+BPSK'
        elif rmode == 0x01:
            type = '20:CH1+BPSK'
        elif rmode == 0x02:
            type = '40:CH2+BPSK'
        elif rmode == 0x03:
            type = '80:CH3+BPSK'
        elif rmode == 0x04:
            type = '11:CH0+DS15'
        elif rmode == 0x05:
            type = '21:CH1+DS15'
        elif rmode == 0x06:
            type = '41:CH2+DS15'
        elif rmode == 0x07:
            type = '81:CH3+DS15'
        elif rmode == 0x08:
            type = '12:CH0+DS63'
        elif rmode == 0x09:
            type = '22:CH1+DS63'
        elif rmode == 0x0A:
            type = '42:CH2+DS63'
        elif rmode == 0x0B:
            type = '82:CH3+DS63'
        elif rmode == 0x0C:
            type = 'F0:SALVO+BPSK'
        elif rmode == 0x0D:
            type = 'F1:SALVO+DS15'
        elif rmode == 0x0E:
            type = 'F2:SALVO+DS63'
        else:
            type = 'ERROR DISP Mode!!'
    return type


def check_bit(value, bit):
    # �ж�value�ĵ�bitλ�Ƿ�Ϊ1
    if value & 0x01<<bit:
        return True
    else:
        return False

class PowerMesh():
    '''A powermesh frame object
    '''
    FIRM_VER = 1
    LEN_PPCI = 5
    MAX_PHY_LEN = 300

    def __init__(self, phy_data='', encode='asc_hex'):
        '''establish a powermesh obj by a frame of rcv_loop phy data or nothing('', for generate a phy frame)
        :param phy_data: received phy frame, usually consisted of asc hex string
        :param encode: format of phy_data, default 'asc_hex', other option: 'str', 'dec_list'
        :return:
        '''
        if phy_data != '' and encode == 'asc_hex':
            self.data = POWERMESH_INNER_DATA_TYPE(asc_hex_str_to_dec_array(phy_data))

        pass

    @staticmethod
    def parse(phy_data, encode='asc_hex'):
        # ��Ƴɾ�̬����, �Ա�ֱ�ӵ���
        if phy_data != '' and encode == 'asc_hex':
            phy_data = POWERMESH_INNER_DATA_TYPE(asc_hex_str_to_dec_array(phy_data))
            
        if len(phy_data) < 4:
            print u'��������ݰ�����, Ӧ����4�ֽ�'

        print("================================\nPHY Layer:")
        if len(phy_data) == 4:
            # SRF���ݰ�
            cs = (256 - (sum(phy_data[:-1]) % 256)) % 256
            disturb = (phy_data[-1] - cs) % 256
            first_byte = phy_data[0]
            
            print u"����ΪSRF���ݰ�, ����%02X" % (disturb)
            
            if check_bit(first_byte,7):
                print u'ESF���ݰ�'
                print phy_data
                print u'NAVֵ0x%04X' % (phy_data[1] * 256 + phy_data[2])
                return
            elif check_bit(first_byte,2):
                print(u'SRF���ݰ�, Ӧ����EBC��SBRF��Ӧ֡')
                if check_bit(first_byte,3):
                    print(u'SCAN����, �汾��0x%02X' % (first_byte % 4))
                else:
                    print(u'��scan����, �汾��0x%02X' % (first_byte % 4))
            else:
                print(u'����SRF���ݰ�����,��û�б�־λ')
                return
                
                
            #  check freq
            a = first_byte>>4
            if (a % 8) >= 4:
                print(u'Ƶ��ͨ��:��ͨ��')
            else:
                print(u'Ƶ��ͨ��:CH%02X' % (a % 8))
            
            print(u'�㲥ID:0x%02X' % (phy_data[1]>>4))
            print(u'���ID:0x%04X' % ((phy_data[1] % 16)*256 + phy_data[2]))
        else:
            #��ͨ���ݰ�
            ## PHY ����
            cs = (256 - (sum(phy_data[0:9]) % 256)) % 256
            disturb = (phy_data[9] - cs) % 256
            first_byte = phy_data[0]
            
            if crc16(phy_data[:-1]+[phy_data[-1]^disturb]) != [0xE2, 0xF0]:
                phy_data = powermesh_rscodec.rsdecode_vec(phy_data)
                if crc16(phy_data[:-1]+[phy_data[-1]^disturb]) == [0xE2, 0xF0]:
                    datarate = 0
                    print(u"RS�����У��ͨ��! BPSK����, ����0x%02X" % disturb)
                else:
                    print(u"crc У�����")
                    return
            else:
                datarate = 1
                print(u'crcУ��ͨ��!����0x%02X,��RS����' % disturb)
            
            ## check scan
            if check_bit(first_byte, 3):
                scan = 1
                print(u'SCAN, �汾��0x%02X' % (first_byte % 4))
            else:
                scan = 0
                print(u'��SCAN, �汾��0x%02X' % (first_byte % 4))
            
            ## check srf
            if check_bit(first_byte,  2):
                print(u'������SRF��־,����!')
                return
            
            ## check freq
            a = int(first_byte/16)
            if a >= 8:
                print(u'����㳤������')
            if (a % 8) >= 4:
                print(u'Ƶ��ͨ��:��ͨ��')
            else:
                print(u'Ƶ��ͨ��:CH%d' % (a % 8))
            
            if datarate == 0:
                print(u'����: ��RS����, ������BPSK')
            else:
                print(u'����: ��RS����, ������DS15��DS63')
            print(u'����㳤��:%d Bytes' % len(phy_data))
            
            
            ## DLL����
            print('--------\nDLL Layer:')
            ind_len = int(first_byte/128)*256 + phy_data[1]
            if ind_len != len(phy_data):
                print(u'������Ϣ����')
                return
            if (sum(phy_data[:10])-disturb) % 256 != 0:
                print(u'CSУ�鲻��')
                return
            
            print(u'Ŀ�ĵ�ַUID:%02X%02X%02X%02X%02X%02X' % (phy_data[3], phy_data[4], phy_data[5], phy_data[6], phy_data[7], phy_data[8]))
            print(u'Դ��ַUID:%02X%02X%02X%02X%02X%02X' % (phy_data[10], phy_data[11], phy_data[12], phy_data[13], phy_data[14], phy_data[15]))
            dlct = phy_data[9]
            
            if check_bit(dlct, 7):
                if (dlct % 64)>>2 == 15:
                    print(u'DLLЭ��:��չDLLЭ��(EDP)')
                    lsdu = phy_data[16:-2]
                    if lsdu[0] >> 6 == 1:
                        print(u'Э��:EBC\n֡����')
                        if lsdu[0] % 4 == 0:
                            print(u'EBC�㲥֡(NBF)')
                            print(u'Ҫ�󷵻�����:0x%s' % response_mode(lsdu[0],scan))
                            print(u'�㲥ID:0x%02X' % (lsdu[1]>>4))
                            print(u'������:%d' % 2**(lsdu[1]%16))
                            print(u'��ӦMASK:%8s (X X BUILD_ID METER_ID UID SNR SS AC_PHASE)' % bin(lsdu[2])[2:])
                            print(u'��Ӧ����: %s' % dec_array_to_asc_hex_str(lsdu[3:], ' '))
                        elif lsdu[0] % 4 == 1:
                            print(u'EBC���ID��ѯ֡(NIF)')
                            print(u'Ҫ�󷵻�����:0x%s' % response_mode(lsdu[0],scan))
                            print(u'�㲥ID:0x%02X' % (lsdu[1]>>4))
                            print(u'���ID:0x%04X' % ((lsdu[1] % 16)*256 + lsdu[2]))
                        elif lsdu[0] % 4 == 2:
                            print(u'EBC���ID��Ӧ֡(NAF)')
                            print(u'�㲥ID:0x%02X' % (lsdu[1] >> 4))
                            print(u'���ID:0x%04X' % ((lsdu[1] % 16)*256 + lsdu[2]))
                        elif lsdu[0] % 4 == 3:
                            print(u'EBCȷ��֡(NCF)')
                            print(u'�㲥ID:0x%02X' % (lsdu[1]>>4))
                            print(u'���ID:0x%04X' % ((lsdu[1] % 16)*256 + lsdu[2]))
                        else:
                            print(u'����ʶ���EDP/EBC����֡')
                    else:
                        print(u'��֧�ֵ�EDPЭ��')
                    return
                        
                else:
                    print(u'Diag����')
                    if not check_bit(dlct, 6):
                        print(u'����')
                        print(u'Ҫ�󷵻�����:0x%s' % response_mode(dlct,scan))
                    else:
                        print(u'��Ӧ')
                        print(u'LSDU:'), 
                        print(phy_data[16:-2])
                    print(u'���к�:%d' % (dlct % 4))
                    return
            else:
                print(u'��ͨ����')
                if not check_bit(dlct, 6):
                    print(u'����')
                    if check_bit(dlct, 5):
                        print(u'Ҫ����Ӧ')
                    else:
                        print(u'��Ҫ����Ӧ')
                else:
                    print(u'��Ӧ��')
                print(u'���к�:%d' % (dlct % 4))
            print('LSDU:'), 
            print(phy_data[16:-2])
            
            ##Network����
            lsdu = phy_data[16:-2]
            if not len(lsdu)==0:
                print(u'--------\nNW Layer:')
                if lsdu[0] >> 4 == 6:
                    print(u'�����Э��:PSR')
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
                    print(u'�����Э��:DST')
                    if len(lsdu)<7:
                        print(u'LSDU���ݳ��ȴ���%d' % len(lsdu))

                    conf = lsdu[0]
                    jumps = lsdu[1]
                    forward = lsdu[2]
                    
                    print(u'flood id:0x%02X' % (conf % 4))
                    if check_bit(conf,3):
                        print(u'Flooding Search,')
                    else:
                        print(u'Flooding transmit,')
                    
                    if check_bit(conf,2):
                        print(u'����')
                    else:
                        print(u'����')

                    print(u'������:%d,ʣ������%d' % (jumps>>4, jumps%16))
                    
                    if check_bit(forward,4):        #check acps_ena
                        print(u'��λԼ��,ת��Я��ACPS:0x%02X' % lsdu[3])
                    
                    if check_bit(forward,5):        #check network_id_ena
                        print(u'����Լ��,ת��Я������ID:0x%02X' % lsdu[4])
                    
                    if forward % 8:
                        print(u'��%d��,ת��������:%d,���ڴ������к�:%d' % int(jumps/16) - mod(jumps % 16), 2**(forward % 8), lsdu[5])
                    
                    if check_bit(forward,3):
                        print(u'ת�����ڵݼ�ʹ��')
                    
                    print(u'NSDU(%d bytes):%s' % (len(lsdu[6:]), dec_array_to_asc_hex_str(lsdu[6:])))
                    
                elif (lsdu[0] >> 4)==15:
                    print(u'�����Э��:PTP')
                    print(u'NSDU(%d bytes):%s' % (len(lsdu[1:]), dec_array_to_asc_hex_str(lsdu[1:])))
                else:
                    print(u'�޷�ʶ��������Э��')
                
    @staticmethod
    def phy_gen(psdu, xmode, scan = False, srf = False):
        ''' ����phy֡
        xmode: ��4λ��Ƶ��, ��2λ������
                0x1X: CH0   0xX0: BPSK
                0x2X: CH1   0xX1: DS15
                0x4X: CH2   0xX2: DS63
                0x8X: CH3
                0xFX: SALVO
        if scan is True, the ch indication in PHPR is
        '''

        assert (xmode & 0xF0 in (0x10, 0x20, 0x40, 0x80, 0xF0) and xmode % 4 in (0x00, 0x01, 0x02)), "error xmode 0x%02X" % xmode
        phy_len = len(psdu) + PowerMesh.LEN_PPCI
        assert phy_len <= PowerMesh.MAX_PHY_LEN, "error phy len %d" % phy_len

        phpr = PowerMesh.FIRM_VER \
                + (0x04 if srf else 0) \
                + (0x08 if scan else 0) \
                + ({0x10:0,0x20:1,0x40:2,0x80:3,0xF0:4}[xmode & 0xF0] << 4) \
                + (0x80 if phy_len > 255 else 0)

        if not srf:
            sec_len = phy_len % 256
            cs = -(phpr + sec_len + sum(psdu[0:7])) % 256

            ppdu = [phpr] + [phy_len] + [cs] + psdu
            ppdu += crc16(ppdu)
        else:
            cs = -(phpr + sum(psdu[0:2])) % 256
            ppdu = [phpr] + psdu[0:2] + [cs]

        return POWERMESH_INNER_DATA_TYPE(ppdu)

    @staticmethod
    def dll_gen(lsdu, src_uid, target_uid, prop):
        ''' ����dll֡
        lsdu: ...
        src_uid: 12 bytes asc_hex string
        target_uid: 12 bytes asc_hex string
        prop:
        '''
        pass

    def gen_dll_frame(lsdu):
        pass
    def gen_nw_frame(nsdu):
        pass
    def gen_app_frame(asdu):
        pass

if __name__ == '__main__':
    import time
    # print list(crc16(POWERMESH_INNER_DATA_TYPE([173,   101,    94,   252,     9,   226,   233,   203,    25,    67,    85,   174,    34,   184,    27])))
    # print asc_hex_str_to_dec_array('12345678')

    p = PowerMesh()
#    p.parse('3D79E664')
#     p.parse('091724000000000000BC17BCF5CA2B36582F436A4307622934027075215343939A6BF153D516DD5EC7739E9BDC0B703970F53E16E7')
    # p.parse('313E88430762293400005E1D0A05857C60332A0011250E68210113091000689118343439389C83363333333333C6BC343333333333A99334334C16006162')
#    p.parse('0912055E1D0A077584B09ACCA0BB52331E907E814307612234026C25F0B2DA3045CE69628D9B')
    
    # p.parse('3917F4000000000000BCB079B27FA54415867A01430762293402707521190DA72B2F174C0554A505C7710F6AC78615C29E9931705B')
    # p.parse('3D78C388')
    # p.parse('091526000000000000BCE3376AFDB8CDE890DF1D43076229340271781FFE52ACA04BA104E412E3484975A491B1BA8E698EC810')
    # p.parse('3915AB430762293402FC5E1D0A04878242781F4898')
    # p.parse('19158B5E1D0A048082BCD13DE35FCB55EC554A30430762293402437439C59745B85C9922C32F509A4975A491B1BA8E698EC810')

    text = '3915AB430762293402FC5E1D0A04878242781F4898'
    print text

    a = asc_hex_str_to_dec_array(text)
    #a = powermesh_rscodec.rsdecode_vec(a)
    a = dec_array_to_asc_hex_str(p.phy_gen(a[3:-2], 0x81, scan = 1, srf = 1))
    print a
    p.parse(a)

    print "\n-------\nTHE END"
    time.sleep(0.1)
    pass
