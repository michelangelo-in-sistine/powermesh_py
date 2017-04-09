# -*- coding: cp936 -*-
# file: manufacturing_test_suite.py
# author: Lv Haifeng
# ver: 1.0
# 2017-01-30
"""
    PvMesh SS模块加工测试程序
    python交互环境下，首先导入manufacturing_test_suite
    >>import manufacturing_test_suite as mts
    然后执行
    >>mts.main()
    即自动执行以下流程:
    1. 模块程序烧写
    2. 模块通信性能测试
    3. 模块电压电流温度测量校准
    4. 打印标签

    使用前先按实际配置情况修改文件中的配置信息（串口号, 文件路径）
"""

#######################################################################
# 配置信息, 执行前先按实际情况修改成正确设置

## 烧录的hex文件路径
HEX_IMAGE = r'e:\unify_root\project\pv_mon\firmware\deliver\2017-03-05 修改了热敏B,修改了内部版本日期, python增加plc读uid\powermesh_ss.hex'
SS_VERSION = '2017.03.05'

# 连接CV的串口
PORT_CV = 'com4'

# 连接编程器的串口
PORT_PROGRAMMER = 'com8'

# 连接程控电源的串口, 还需要设置正确的波特率, 数据位, 停止位, 奇偶校验
# e.g. 安捷伦电源E3631A的配置为: serial.Serial(COMx, baudrate = 9600, bytesize=8, parity='N', stopbits=2);
PORT_POWER_SUPPLY = 'com4'

# 标签打印机串口
PORT_TAG_PRINTER = 'com2'

# 电压校准点0,1
CALIB_POINT_VOLT_0 = 24        # Point 0. 24(V)
CALIB_POINT_VOLT_1 = 10        # Point 1. 10(V)

# 电流校准点0,1
CALIB_POINT_CURT_0 = 4.8        # Point 0. 4800(mA)
CALIB_POINT_CURT_1 = 0.5        # Point 1. 500(mA)

# 温度校准点0,1
CALIB_POINT_TEMP_0 = 4.5        # Point 0. 4.5(V)
CALIB_POINT_TEMP_1 = 0.5        # Point 1. 0.5(V)

# 通信信噪比阈值
# 测试通信性能时会得到经过衰减器后的通信信号强度和信噪比, 必须满足指定门限，否则认为通信电路不正常
CH_CARE = ('ch1','ch2','ch3')   # 通信性能测试关注的频率, CH0信噪比测量不准， 不用看
SS_GATE = 70                    # 信号强度门限, 单位dBuV, 所有关注的通信频率的全部上下行信号强度都必须不小于此门限方为合格
SNR_GATE = 40                   # 通信信噪比门限, 单位dB, 所有关注的通信频率的全部上下行信噪比都必须不小于此门限方为合格

# 电压电流温度校准寄存器范围
# PLC校准时会携带此时的寄存器值，对此寄存器值进行检查，偏差太大认为是测量电路的元器件参数错误，认为不合格
CALIB_POINT_VOLT_0_REG = 173828   # 电压校正的寄存器参考值1, 理想参考值为V/(51e3+50)*50*8/0.7*2^20, 应以实际测量值为准
CALIB_POINT_VOLT_0_REG_TOL = 0.2   # 允许寄存器上下浮动的范围，0.2为百分之二十
CALIB_POINT_VOLT_1_REG = 0x400000   # 电压校正的寄存器参考值2
CALIB_POINT_VOLT_1_REG_TOL = 0.2   # 允许寄存器上下浮动的范围，0.2为百分之二十
CALIB_POINT_CURT_0_REG = 0x100000   # 电流校正的寄存器参考值, I*r*16/0.7*2^20
CALIB_POINT_CURT_0_REG_TOL = 0.2       # 允许寄存器上下浮动的范围
CALIB_POINT_CURT_1_REG = 0x100000   # 电流校正的寄存器参考值
CALIB_POINT_CURT_1_REG_TOL = 0.2       # 允许寄存器上下浮动的范围
CALIB_POINT_TEMP_0_REG = 0x100000   # 温度校正的寄存器参考值,
CALIB_POINT_TEMP_0_REG_TOL = 0.2       # 允许寄存器上下浮动的范围
CALIB_POINT_TEMP_1_REG = 0x100000   # 温度校正的寄存器参考值
CALIB_POINT_TEMP_1_REG_TOL = 0.2       # 允许寄存器上下浮动的范围
POWER_SUPPLY_STABLE_TIME = 0.5        # 调整电压电流值后等待稳定时间

#######################################################################

from pyFlashProgrammer import FlashProgrammer
from pvm_interface import CV, PvmException
from serial import Serial
import time

def calib_v_i_t():
    pass


def test_plc_performance(cv, target_uid):
    """ 测试DUT的PLC通信性能
        要求必须指定的信道的信号强度，信噪比达到门限
        否则raise exception
    """
    result = cv.diag(target_uid)
    if result is None:
        print u'待测模块PLC Diag无响应，须修理通信电路'
        raise Exception('Diag Failed')

    ss = []
    snr = []
    for i in range(4):
        if 'ch'+str(i) in CH_CARE:
            ss.append(result[i*2])          # 下行信号强度
            ss.append(result[i*2 + 8])      # 上行信号强度
            snr.append(result[i*2 + 1])     # 下行信噪比
            snr.append(result[i*2 + 9])     # 上行信噪比

    print "min ss", min(ss), "min snr", min(snr)
    if min(ss) < SS_GATE:
        print u'没有达到最小信号幅度要求，须检查通信电路(要求%d, 实际%d)' % (SS_GATE, min(ss))
        raise Exception('ss requirment not achieved')

    if min(snr) < SNR_GATE:
        print u'没有达到最小信噪比要求，须检查通信电路(要求%d, 实际%d)' % (SNR_GATE, min(snr))
        raise Exception('snr requirment not achieved')


def init_power_supply(ps):
    """ 初始化电源设置，给模块上电，用于烧录程序
        TODO：改成实际使用的电源的控制代码
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
    """ 设置程控源输出指定电压, 以E3631为例
        TODO：改成实际使用的电源的控制代码
    """
    ps.write('APPL P25V, %.2f\n') % voltage
    ps.write('OUTP ON\n')


def set_power_supply_current(ps, current):
    """ 设置程控源输出指定电流
        TODO：改成实际使用的电源的控制代码
    """
    pass


def set_power_supply_temperature(ps, temp):
    """ 设置程控源输出指定电压，用于设置温度测量校准点，以E3631为例
        TODO：改成实际使用的电源的控制代码
    """
    ps.write('SYST:REM\n')
    ps.write('*RST\n')
    ps.write('*CLS\n')
    ps.write('APPL P6V, %.2f\n') % temp
    ps.write('OUTP ON\n')


def check_reg(reg, reg_ref, tol):
    if reg is None:
        print u'校正通信失败'
        raise Exception('calibration communication failed')
    else:
        if reg < reg_ref * (1-tol) or reg > reg_ref * (1+tol):
            raise
        else:
            print u'返回寄存器数值在合理范围'


def calibrate(cv, ps, target_uid):
    """ 校正电压电流温度
    """

    ## 电压校正
    set_power_supply_voltage(ps, CALIB_POINT_VOLT_0)
    time.sleep(POWER_SUPPLY_STABLE_TIME)                       #电压稳定时间
    reg = cv.calib_ss_voltage_by_uid(target_uid, 0, CALIB_POINT_VOLT_0)
    check_reg(reg, CALIB_POINT_VOLT_0_REG, CALIB_POINT_VOLT_0_REG_TOL)

    set_power_supply_voltage(ps, CALIB_POINT_VOLT_1)
    time.sleep(POWER_SUPPLY_STABLE_TIME)
    reg = cv.calib_ss_voltage_by_uid(target_uid, 1, CALIB_POINT_VOLT_1)
    check_reg(reg, CALIB_POINT_VOLT_1_REG, CALIB_POINT_VOLT_1_REG_TOL)
    print u'电压校正完成'

    ## 电流校正
    set_power_supply_current(ps, CALIB_POINT_CURT_0)
    time.sleep(POWER_SUPPLY_STABLE_TIME)
    reg = cv.calib_ss_current_by_uid(target_uid, 0, CALIB_POINT_CURT_0)
    check_reg(reg, CALIB_POINT_CURT_0_REG, CALIB_POINT_CURT_0_REG_TOL)

    set_power_supply_current(ps, CALIB_POINT_CURT_1)
    time.sleep(POWER_SUPPLY_STABLE_TIME)
    reg = cv.calib_ss_current_by_uid(target_uid, 1, CALIB_POINT_CURT_1)
    check_reg(reg, CALIB_POINT_CURT_1_REG, CALIB_POINT_CURT_1_REG_TOL)
    print u'电流校正完成'

    set_power_supply_temperature(ps, CALIB_POINT_TEMP_0)
    time.sleep(POWER_SUPPLY_STABLE_TIME)
    reg = cv.calib_ss_temperature_by_uid(target_uid, 0, CALIB_POINT_TEMP_0)
    check_reg(reg, CALIB_POINT_TEMP_0_REG, CALIB_POINT_TEMP_0_REG_TOL)

    # 温度校正
    set_power_supply_temperature(ps, CALIB_POINT_TEMP_1)
    time.sleep(POWER_SUPPLY_STABLE_TIME)
    reg = cv.calib_ss_temperature_by_uid(target_uid, 1, CALIB_POINT_TEMP_1)
    check_reg(reg, CALIB_POINT_TEMP_1_REG, CALIB_POINT_TEMP_1_REG_TOL)
    print u'温度校正完成'

    ret = cv.save_ss_calib_by_uid(target_uid)
    if ret is None:
        print u'保存校正系数发生错误'
        raise Exception('save calib parameters fail')

    print u"校正完成"


def print_tag(tp, target_uid, SS_VERSION):
    """ 打印标签, SS_VERSION为模块软件版本
        TODO: 此处示范为Zebra标签打印机的控制，须改成实际使用的打印机控制代码
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
    ### TODO: 电源控制串口，须修改成实际电源配置
    # ps = Serial(PORT_POWER_SUPPLY, baudrate = 9600, bytesize=8, parity='N', stopbits=2)
    # init_power_supply(ps)
    #########################################

    ###***********************************###
    ### TODO: 便签打印，须改成实际打印机控制配置
    # tp = Serial(PORT_TAG_PRINTER, baudrate = 9600, bytesize=8, parity='N', stopbits=1)

    try:
        # Step 0. 给DUT上电
        # init_power_supply()
        # time.sleep(0.5)

        # Step 1. 读取芯片UID，烧写程序
        for i in xrange(4):
            fp.clear_uart()
            target_uid = fp.read_uid()
            fp.full_main_array_burn(HEX_IMAGE)
            time.sleep(0.5)                         # 模块复位时间

            # Step 2. 测试通信性能
            test_plc_performance(cv, target_uid)
            time.sleep(0.1)

            # Step 3. 校准模块测量
            # calibrate(cv, ps, target_uid)

            # Step 4. 打印标签
            # print_tag(tp, target_uid, SS_VERSION)

            print u'DUT测试通过！'
            raw_input()

    except Exception as e:
        print "Exception Occurred:", type(e), str(e)

    finally:
        cv.close()
        fp.close()
        # close_power_supply()     #测试完一定要关闭电源，防止电源带电接插模块，那将有可能烧坏模块电源芯片
        # ps.close()
        # tp.close()


if '__main__' == __name__:
    main()
