# -*- coding: cp936 -*-
# file: manufacturing_test_suite.py
# author: Lv Haifeng
# ver: 1.0
# 2017-01-30
"""
    PvMesh SSģ��ӹ����Գ���
    python���������£����ȵ���manufacturing_test_suite
    >>import manufacturing_test_suite as mts
    Ȼ��ִ��
    >>mts.main()
    ���Զ�ִ����������:
    1. ģ�������д
    2. ģ��ͨ�����ܲ���
    3. ģ���ѹ�����¶Ȳ���У׼
    4. ��ӡ��ǩ

    ʹ��ǰ�Ȱ�ʵ����������޸��ļ��е�������Ϣ�����ں�, �ļ�·����
"""

#######################################################################
# ������Ϣ, ִ��ǰ�Ȱ�ʵ������޸ĳ���ȷ����

## ��¼��hex�ļ�·��
HEX_IMAGE = r'e:\unify_root\project\pv_mon\firmware\deliver\2017-03-05 �޸�������B,�޸����ڲ��汾����, python����plc��uid\powermesh_ss.hex'
SS_VERSION = '2017.03.05'

# ����CV�Ĵ���
PORT_CV = 'com4'

# ���ӱ�����Ĵ���
PORT_PROGRAMMER = 'com8'

# ���ӳ̿ص�Դ�Ĵ���, ����Ҫ������ȷ�Ĳ�����, ����λ, ֹͣλ, ��żУ��
# e.g. �����׵�ԴE3631A������Ϊ: serial.Serial(COMx, baudrate = 9600, bytesize=8, parity='N', stopbits=2);
PORT_POWER_SUPPLY = 'com4'

# ��ǩ��ӡ������
PORT_TAG_PRINTER = 'com2'

# ��ѹУ׼��0,1
CALIB_POINT_VOLT_0 = 24        # Point 0. 24(V)
CALIB_POINT_VOLT_1 = 10        # Point 1. 10(V)

# ����У׼��0,1
CALIB_POINT_CURT_0 = 4.8        # Point 0. 4800(mA)
CALIB_POINT_CURT_1 = 0.5        # Point 1. 500(mA)

# �¶�У׼��0,1
CALIB_POINT_TEMP_0 = 4.5        # Point 0. 4.5(V)
CALIB_POINT_TEMP_1 = 0.5        # Point 1. 0.5(V)

# ͨ���������ֵ
# ����ͨ������ʱ��õ�����˥�������ͨ���ź�ǿ�Ⱥ������, ��������ָ�����ޣ�������Ϊͨ�ŵ�·������
CH_CARE = ('ch1','ch2','ch3')   # ͨ�����ܲ��Թ�ע��Ƶ��, CH0����Ȳ�����׼�� ���ÿ�
SS_GATE = 70                    # �ź�ǿ������, ��λdBuV, ���й�ע��ͨ��Ƶ�ʵ�ȫ���������ź�ǿ�ȶ����벻С�ڴ����޷�Ϊ�ϸ�
SNR_GATE = 40                   # ͨ�����������, ��λdB, ���й�ע��ͨ��Ƶ�ʵ�ȫ������������ȶ����벻С�ڴ����޷�Ϊ�ϸ�

# ��ѹ�����¶�У׼�Ĵ�����Χ
# PLCУ׼ʱ��Я����ʱ�ļĴ���ֵ���Դ˼Ĵ���ֵ���м�飬ƫ��̫����Ϊ�ǲ�����·��Ԫ��������������Ϊ���ϸ�
CALIB_POINT_VOLT_0_REG = 173828   # ��ѹУ���ļĴ����ο�ֵ1, ����ο�ֵΪV/(51e3+50)*50*8/0.7*2^20, Ӧ��ʵ�ʲ���ֵΪ׼
CALIB_POINT_VOLT_0_REG_TOL = 0.2   # ����Ĵ������¸����ķ�Χ��0.2Ϊ�ٷ�֮��ʮ
CALIB_POINT_VOLT_1_REG = 0x400000   # ��ѹУ���ļĴ����ο�ֵ2
CALIB_POINT_VOLT_1_REG_TOL = 0.2   # ����Ĵ������¸����ķ�Χ��0.2Ϊ�ٷ�֮��ʮ
CALIB_POINT_CURT_0_REG = 0x100000   # ����У���ļĴ����ο�ֵ, I*r*16/0.7*2^20
CALIB_POINT_CURT_0_REG_TOL = 0.2       # ����Ĵ������¸����ķ�Χ
CALIB_POINT_CURT_1_REG = 0x100000   # ����У���ļĴ����ο�ֵ
CALIB_POINT_CURT_1_REG_TOL = 0.2       # ����Ĵ������¸����ķ�Χ
CALIB_POINT_TEMP_0_REG = 0x100000   # �¶�У���ļĴ����ο�ֵ,
CALIB_POINT_TEMP_0_REG_TOL = 0.2       # ����Ĵ������¸����ķ�Χ
CALIB_POINT_TEMP_1_REG = 0x100000   # �¶�У���ļĴ����ο�ֵ
CALIB_POINT_TEMP_1_REG_TOL = 0.2       # ����Ĵ������¸����ķ�Χ
POWER_SUPPLY_STABLE_TIME = 0.5        # ������ѹ����ֵ��ȴ��ȶ�ʱ��

#######################################################################

from pyFlashProgrammer import FlashProgrammer
from pvm_interface import CV, PvmException
from serial import Serial
import time

def calib_v_i_t():
    pass


def test_plc_performance(cv, target_uid):
    """ ����DUT��PLCͨ������
        Ҫ�����ָ�����ŵ����ź�ǿ�ȣ�����ȴﵽ����
        ����raise exception
    """
    result = cv.diag(target_uid)
    if result is None:
        print u'����ģ��PLC Diag����Ӧ��������ͨ�ŵ�·'
        raise Exception('Diag Failed')

    ss = []
    snr = []
    for i in range(4):
        if 'ch'+str(i) in CH_CARE:
            ss.append(result[i*2])          # �����ź�ǿ��
            ss.append(result[i*2 + 8])      # �����ź�ǿ��
            snr.append(result[i*2 + 1])     # ���������
            snr.append(result[i*2 + 9])     # ���������

    print "min ss", min(ss), "min snr", min(snr)
    if min(ss) < SS_GATE:
        print u'û�дﵽ��С�źŷ���Ҫ������ͨ�ŵ�·(Ҫ��%d, ʵ��%d)' % (SS_GATE, min(ss))
        raise Exception('ss requirment not achieved')

    if min(snr) < SNR_GATE:
        print u'û�дﵽ��С�����Ҫ������ͨ�ŵ�·(Ҫ��%d, ʵ��%d)' % (SNR_GATE, min(snr))
        raise Exception('snr requirment not achieved')


def init_power_supply(ps):
    """ ��ʼ����Դ���ã���ģ���ϵ磬������¼����
        TODO���ĳ�ʵ��ʹ�õĵ�Դ�Ŀ��ƴ���
    """
    ps.write('SYST:REM\n')
    ps.write('*RST\n')
    ps.write('*CLS\n')
    ps.write('APPL P25V, 12.0\n')
    ps.write('OUTP ON\n')


def close_power_supply(ps):
    ps.write('SYST:REM\n')
    ps.write('*RST\n')
    ps.write('*CLS\n')
    ps.write('OUTP OFF\n')



def set_power_supply_voltage(ps, voltage):
    """ ���ó̿�Դ���ָ����ѹ, ��E3631Ϊ��
        TODO���ĳ�ʵ��ʹ�õĵ�Դ�Ŀ��ƴ���
    """
    ps.write('APPL P25V, %.2f\n') % voltage
    ps.write('OUTP ON\n')


def set_power_supply_current(ps, current):
    """ ���ó̿�Դ���ָ������
        TODO���ĳ�ʵ��ʹ�õĵ�Դ�Ŀ��ƴ���
    """
    pass


def set_power_supply_temperature(ps, temp):
    """ ���ó̿�Դ���ָ����ѹ�����������¶Ȳ���У׼�㣬��E3631Ϊ��
        TODO���ĳ�ʵ��ʹ�õĵ�Դ�Ŀ��ƴ���
    """
    ps.write('SYST:REM\n')
    ps.write('*RST\n')
    ps.write('*CLS\n')
    ps.write('APPL P6V, %.2f\n') % temp
    ps.write('OUTP ON\n')


def check_reg(reg, reg_ref, tol):
    if reg is None:
        print u'У��ͨ��ʧ��'
        raise Exception('calibration communication failed')
    else:
        if reg < reg_ref * (1-tol) or reg > reg_ref * (1+tol):
            raise
        else:
            print u'���ؼĴ�����ֵ�ں���Χ'


def calibrate(cv, ps, target_uid):
    """ У����ѹ�����¶�
    """

    ## ��ѹУ��
    set_power_supply_voltage(ps, CALIB_POINT_VOLT_0)
    time.sleep(POWER_SUPPLY_STABLE_TIME)                       #��ѹ�ȶ�ʱ��
    reg = cv.calib_ss_voltage_by_uid(target_uid, 0, CALIB_POINT_VOLT_0)
    check_reg(reg, CALIB_POINT_VOLT_0_REG, CALIB_POINT_VOLT_0_REG_TOL)

    set_power_supply_voltage(ps, CALIB_POINT_VOLT_1)
    time.sleep(POWER_SUPPLY_STABLE_TIME)
    reg = cv.calib_ss_voltage_by_uid(target_uid, 1, CALIB_POINT_VOLT_1)
    check_reg(reg, CALIB_POINT_VOLT_1_REG, CALIB_POINT_VOLT_1_REG_TOL)
    print u'��ѹУ�����'

    ## ����У��
    set_power_supply_current(ps, CALIB_POINT_CURT_0)
    time.sleep(POWER_SUPPLY_STABLE_TIME)
    reg = cv.calib_ss_current_by_uid(target_uid, 0, CALIB_POINT_CURT_0)
    check_reg(reg, CALIB_POINT_CURT_0_REG, CALIB_POINT_CURT_0_REG_TOL)

    set_power_supply_current(ps, CALIB_POINT_CURT_1)
    time.sleep(POWER_SUPPLY_STABLE_TIME)
    reg = cv.calib_ss_current_by_uid(target_uid, 1, CALIB_POINT_CURT_1)
    check_reg(reg, CALIB_POINT_CURT_1_REG, CALIB_POINT_CURT_1_REG_TOL)
    print u'����У�����'

    set_power_supply_temperature(ps, CALIB_POINT_TEMP_0)
    time.sleep(POWER_SUPPLY_STABLE_TIME)
    reg = cv.calib_ss_temperature_by_uid(target_uid, 0, CALIB_POINT_TEMP_0)
    check_reg(reg, CALIB_POINT_TEMP_0_REG, CALIB_POINT_TEMP_0_REG_TOL)

    # �¶�У��
    set_power_supply_temperature(ps, CALIB_POINT_TEMP_1)
    time.sleep(POWER_SUPPLY_STABLE_TIME)
    reg = cv.calib_ss_temperature_by_uid(target_uid, 1, CALIB_POINT_TEMP_1)
    check_reg(reg, CALIB_POINT_TEMP_1_REG, CALIB_POINT_TEMP_1_REG_TOL)
    print u'�¶�У�����'

    ret = cv.save_ss_calib_by_uid(target_uid)
    if ret is None:
        print u'����У��ϵ����������'
        raise Exception('save calib parameters fail')

    print u"У�����"


def print_tag(tp, target_uid, SS_VERSION):
    """ ��ӡ��ǩ, SS_VERSIONΪģ������汾
        TODO: �˴�ʾ��ΪZebra��ǩ��ӡ���Ŀ��ƣ���ĳ�ʵ��ʹ�õĴ�ӡ�����ƴ���
    """
    tp.write("^XA\n")
    tp.write("^PRA~SD10\n")

    tp.write("^FO65, 20\n^A0,30,20^FD")
    tp.write("SS_VER: ")
    tp.write(SS_VERSION)

    tp.write("^FS\n^FO65,60^BY1\n^BCN,75,N,N,N\n^FD")
    tp.write(target_uid)

    tp.write("^FS\n^FO65,150\n^A0,50,25^FD")
    tp.write(target_uid)

    tp.write("^FS\n")
    tp.write("^XZ\n")


def main():
    cv = CV(PORT_CV)
    fp = FlashProgrammer(PORT_PROGRAMMER)

    #########################################
    ### TODO: ��Դ���ƴ��ڣ����޸ĳ�ʵ�ʵ�Դ����
    # ps = Serial(PORT_POWER_SUPPLY, baudrate = 9600, bytesize=8, parity='N', stopbits=2)
    # init_power_supply(ps)
    #########################################

    ###***********************************###
    ### TODO: ��ǩ��ӡ����ĳ�ʵ�ʴ�ӡ����������
    # tp = Serial(PORT_TAG_PRINTER, baudrate = 9600, bytesize=8, parity='N', stopbits=1)

    try:
        # Step 0. ��DUT�ϵ�
        # init_power_supply()
        # time.sleep(0.5)

        # Step 1. ��ȡоƬUID����д����
        for i in xrange(4):
            fp.clear_uart()
            target_uid = fp.read_uid()
            fp.full_main_array_burn(HEX_IMAGE)
            time.sleep(0.5)                         # ģ�鸴λʱ��

            # Step 2. ����ͨ������
            test_plc_performance(cv, target_uid)
            time.sleep(0.1)

            # Step 3. У׼ģ�����
            # calibrate(cv, ps, target_uid)

            # Step 4. ��ӡ��ǩ
            # print_tag(tp, target_uid, SS_VERSION)

            print u'DUT����ͨ����'
            raw_input()

    except Exception as e:
        print "Exception Occurred:", type(e), str(e)

    finally:
        cv.close()
        fp.close()
        # close_power_supply()     #������һ��Ҫ�رյ�Դ����ֹ��Դ����Ӳ�ģ�飬�ǽ��п����ջ�ģ���ԴоƬ
        # ps.close()
        # tp.close()


if '__main__' == __name__:
    main()
