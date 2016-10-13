#!d:\\python27 python2.7
# -*- coding: cp936 -*-

POWERMESH_INNER_DATA_TYPE = list
#test
def asc_hex_to_dec_list(asc_hex_str):
    assert (len(asc_hex_str) % 2 == 0), 'input length error: %s' % (asc_hex_str,)
    temp = [int(asc_hex_str[i:i+2],16) for i in xrange(len(asc_hex_str)) if i % 2 == 0]
    return POWERMESH_INNER_DATA_TYPE(temp)

def crc16(data):
    '''
    :param data: input dec list
    :return:dec list for calce
    '''
    assert(type(data)==POWERMESH_INNER_DATA_TYPE), 'input data must be a %s' % (POWERMESH_INNER_DATA_TYPE,)

    crc = 0xFFFF
    for newbyte in data:
        for j in xrange(8):
            crcbit = 1 if (crc & 0x8000) else 0
            databit = 1 if (newbyte & 0x80) else 0
            crc = (crc<<1) % 0x10000
            if(crcbit != databit):
                crc ^= 0x1021
            newbyte = (newbyte<<1) % 0x100
    crc ^= 0xFFFF

    return POWERMESH_INNER_DATA_TYPE([crc>>8, crc%256])
    
def check_bit(value, bit):
    # �ж�value�ĵ�bitλ�Ƿ�Ϊ1
    if value & 0x01<<bit:
        return True
    else:
        return False

class PowerMesh():
    '''A powermesh frame object
    '''

    def __init__(self, phy_data='', encode='asc_hex'):
        '''establish a powermesh obj by a frame of receiving phy data or nothing('', for generate a phy frame)
        :param phy_data: received phy frame, usually consisted of asc hex string
        :param encode: format of phy_data, default 'asc_hex', other option: 'str', 'dec_list'
        :return:
        '''
        if phy_data != '' and encode == 'asc_hex':
            self.data = POWERMESH_INNER_DATA_TYPE(asc_hex_to_dec_list(phy_data))

        pass;

    @staticmethod
    def parse(phy_data, encode='asc_hex'):
        # ��Ƴɾ�̬����, �Ա�ֱ�ӵ���
        if phy_data != '' and encode == 'asc_hex':
            phy_data = POWERMESH_INNER_DATA_TYPE(asc_hex_to_dec_list(phy_data))
            
        if len(phy_data) < 4:
            print u'��������ݰ�����, Ӧ����4�ֽ�'

        print("--------\nPHY Layer:")
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
            
            print u'�㲥ID:0x%02X' % (phy_data[1]>>4)
            print(u'���ID:0x%04X' % ((phy_data[1] % 16)*256 + phy_data[2]))
        else:
            #��ͨ���ݰ�
            ## PHY ����
            cs = (256 - (sum(phy_data[0:9]) % 256)) % 256
            disturb = (phy_data[9] - cs) % 256
            
            if(crc16(phy_data[:-1]+[phy_data[-1]^disturb]) != [0xE2, 0xF0]):
                print(u'crcУ�����, ������');
                return;
            else:
                datarate = 1;
                print(u'crcУ��ͨ��!����0x%02X,��RS����' % disturb);
#            
#            #     check scan
#            if(check_bit(s(1),3))
#                scan = 1;
#                fprintf('SCAN,');
#                fprintf('�汾��0x%s\n',dec2hexstr(mod(s(1),4)));
#            else
#                scan = 0;
#                fprintf('��scan,');
#                fprintf('�汾��0x%s\n',dec2hexstr(mod(s(1),4)));
#            end
#            
#            #     check srf
#            if(check_bit(s(1),2))
#                fprintf('������SRF��־,����!\n');
#                return;
#            end
#            
#            #     check freq
#            a = floor(s(1)/16);
#            if(a>=8)
#                fprintf('����㳤������\n');
#            end
#            if(mod(a,8)>=4)
#                fprintf('Ƶ��ͨ��:��ͨ��,');
#            else
#                fprintf('Ƶ��ͨ��:CH%d,',mod(a,8));
#            end
#            if(datarate==0)
#                fprintf('����:��RS����, ������BPSK\n');
#            else
#                fprintf('����:��RS����, ������DS15��DS63\n');
#            end
#            fprintf('����㳤��:%d Bytes\n',length(s));
            

if __name__ == '__main__':
    import time
    print list(crc16(POWERMESH_INNER_DATA_TYPE([173,   101,    94,   252,     9,   226,   233,   203,    25,    67,    85,   174,    34,   184,    27])))
    print asc_hex_to_dec_list('12345678')

    p = PowerMesh()
    p.parse('3D79E664')
    p.parse('091724000000000000BC17BCF5CA2B36582F436A4307622934027075215343939A6BF153D516DD5EC7739E9BDC0B703970F53E16E7')
    p.parse('313E88430762293400005E1D0A05857C60332A0011250E68210113091000689118343439389C83363333333333C6BC343333333333A99334334C16006162')
    
    print "\n-------\nTHE END"
    time.sleep(0.1)
    pass
