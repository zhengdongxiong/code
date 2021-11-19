#!/usr/bin/python
import os, sys
import struct
import time

import pa8910_util
from pa8910_util import Version, I2C_DIAG


xint = pa8910_util.xint
debug= pa8910_util.debug
dlog = pa8910_util.dlog
record= pa8910_util.record
param_check=pa8910_util.param_input_check

if I2C_DIAG:
    cpld = pa8910_util.class_cpld_i2c()
    fpga = pa8910_util.class_fpga_i2c()
else:
    cpld = pa8910_util.class_cpld_pci()
    fpga = pa8910_util.class_fpga_pci()


cpld_set_reg = cpld.xset
cpld_get_reg = cpld.xget
fpga_set_reg = fpga.xset
fpga_get_reg = fpga.xget
   

CFG_DDR_SEL      ="0xb00" 
DIAG_ADDR_L      ="0xb40"
DIAG_ADDR_H      ="0xb42"
DIAG_DATA        ="0xb44"
DIAG_ST_MODE     ="0xb46"
DIAG_ST_LOOP     ="0xb48" 
DIAG_CAS         ="0xb4A" 
DIAG_ST_CAS      ="0xb4C" 
DIAG_ST_ECL      ="0xb4E" 
DIAG_ST_ECH      ="0xb50" 
DIAG_ST_EAL      ="0xb52" 
DIAG_ST_EAH      ="0xb54" 
DIAG_ST_EOF      ="0xb56" 
DIAG_ST_ED       ="0xb58" 
DIAG_HPCII_READY ="0xb5A" 
DIAG_WRDAT_CNT_L ="0xb5C" 
DIAG_WRDAT_CNT_H ="0xb5E" 
DIAG_RDDAT_CNT_L ="0xb60" 
DIAG_RDDAT_CNT_H ="0xb62" 
DIAG_RDVLD_CNT_L ="0xb64" 
DIAG_RDVLD_CNT_H ="0xb66" 
DDR_ST_CAS_ENDLESS_NORMAL = "0x0104"
DDR_ST_CAS_LIMITED_NORMAL = "0x0100"
DDR_ST_CAS_ENDLESS_ALTER  = "0x0124"
DDR_ST_CAS_LIMITED_ALTER  = "0x0120"
# DDR_ST_CAS_ENDLESS_NORMAL = "0x0004"
# DDR_ST_CAS_LIMITED_NORMAL = "0x0000"
# DDR_ST_CAS_ENDLESS_ALTER  = "0x0024"
# DDR_ST_CAS_LIMITED_ALTER  = "0x0020"

DDR_ST_CAS_STOP_NORMAL    = "0x0000"
DDR_ST_CAS_STOP_ALTER     = "0x0020"


REG16_MAX = 65535
ddr_mode_type = "0"

#ddr
def show_usage(prog_name):
    prog_name=os.path.basename(prog_name)
    print("====================================")
    print("Version: %s"%Version)
    print("Usage:")
    print("     ./%s start <addr_mode> <mode> <loop> <dimm>" % prog_name)
    print("                 <addr_mode> : 0 ->Normal mode  1 ->Alternating mode")
    print("                 <mode> : (0 to 7)")
    print("                 <loop> : (0: endless other: loop times)")
    print("                 <dimm> : (0 to 3 , all)")
    print("     ./%s stop  <addr_mode> <dimm>" % prog_name)
    print("                <addr_mode> : 0 ->Normal mode  1 ->Alternating mode" )
    print("     ./%s show  <counter/status/rate> <dimm>" % prog_name)
    print("     ./%s show  error <ram_addr> <dimm>" % prog_name)
    print("                <ram_addr> : (0 to 31) ")
    print("     ./%s reset" % prog_name)
    print("     ./%s r <dimm> <addr_32> " % prog_name)
    print("     ./%s w <dimm> <addr_32> <data_32> " % prog_name)
    print("Example:")
    print("     ./%s start 1 3 0" % prog_name)
    print("     ./%s stop 1 "     % prog_name)
    print("     ./%s show counter 1" % prog_name)
    print("     ./%s w 0x11223344 0x55667788 " % prog_name)
    print("     ./%s r 0x11223344 " % prog_name)

def pa8910_fpga_api_ddr_reset():
    fpga_set_reg("0x80", "0x8000")
    time.sleep(0.01)
    fpga_set_reg("0x80", "0")
    print("ddr reset success!")


def pa8910_ddr_diag_start(prog_name, argv):
    param_check(4, argv, show_usage, prog_name)

    addr_mode   = argv.pop( 0 )
    mode_str    = argv.pop( 0 )
    loop_str    = argv.pop( 0 )
    dimm_str    = argv.pop( 0 )

    error = 0
    if xint(mode_str) > 7 :
        print(" mod is illegal (%d), (0 <= mod <= 7)" % (xint(mode_str)))
        error = 1
    if xint(loop_str) > REG16_MAX :
        print(" loop is illegal (%d), (loop <= %d)" % (xint(loop_str), REG16_MAX))
        error = 1
    if(error == 1):
        show_usage( prog_name )
        sys.exit( -1 )

    #reset ddr module 
    pa8910_fpga_api_ddr_reset()
    time.sleep(1)

    ret = _get_ddr_busy(dimm_str)
    if(ret == 1):
        sys.exit( -1 )

    if(dimm_str == "all"):
        fpga_set_reg(CFG_DDR_SEL, "0xf" )
    elif(xint(dimm_str) <= 3):
        fpga_set_reg(CFG_DDR_SEL, dimm_str )
    else:
        print(" dimm is illegal (%d), (dimm = 0,1,2,3,all)" % (xint(dimm_str)))
        show_usage( prog_name )
        sys.exit( -1 )

    fpga_set_reg(DIAG_ST_MODE, mode_str )

    if (addr_mode == "0"):
        if ( xint(loop_str) == 0 ) :
            fpga_set_reg(DIAG_ST_LOOP, "0x2" )
            fpga_set_reg(DIAG_ST_CAS, DDR_ST_CAS_ENDLESS_NORMAL )
        else:
            fpga_set_reg(DIAG_ST_LOOP, loop_str );
            fpga_set_reg(DIAG_ST_CAS, DDR_ST_CAS_LIMITED_NORMAL )
    else:
        if ( xint(loop_str) == 0 ) :
            fpga_set_reg(DIAG_ST_LOOP, "0x2" )
            fpga_set_reg(DIAG_ST_CAS, DDR_ST_CAS_ENDLESS_ALTER )
        else:
            fpga_set_reg(DIAG_ST_LOOP, loop_str );
            fpga_set_reg(DIAG_ST_CAS, DDR_ST_CAS_LIMITED_ALTER )


def pa8910_ddr_diag_stop(prog_name, argv):
    param_check(2, argv, show_usage, prog_name)

    addr_mode = argv.pop( 0 )
    dimm_str  = argv.pop( 0 )
        
    if(dimm_str == "all"):
        fpga_set_reg(CFG_DDR_SEL, "0xf" )
    elif(xint(dimm_str) <= 3):
        fpga_set_reg(CFG_DDR_SEL, dimm_str )
    else:
        print(" dimm is illegal (%d), (dimm = 0,1,2,3,all)" % (xint(dimm_str)))
        show_usage( prog_name )
        sys.exit( -1 )

    if(addr_mode == "0"):
        fpga_set_reg(DIAG_ST_CAS, DDR_ST_CAS_STOP_NORMAL )
    elif (addr_mode == "1"):
        fpga_set_reg(DIAG_ST_CAS, DDR_ST_CAS_STOP_ALTER )
    else:
        show_usage( prog_name )
        sys.exit( -1 )

def _get_ddr_busy(dimm_str):
    if dimm_str == "all":
        fpga_set_reg(CFG_DDR_SEL,"0")
        isbusy0 = (fpga_get_reg(DIAG_ST_CAS)&0x02) >> 1
        if(isbusy0 == 1):
            print("dimm 0 is busy!")
            return 1

        fpga_set_reg(CFG_DDR_SEL,"1")
        isbusy1 = (fpga_get_reg(DIAG_ST_CAS)&0x02) >> 1
        if(isbusy1 == 1):
            print("dimm 1 is busy!")
            return 1

        fpga_set_reg(CFG_DDR_SEL,"2")
        isbusy2 = (fpga_get_reg(DIAG_ST_CAS)&0x02) >> 1
        if(isbusy2 == 1):
            print("dimm 2 is busy!")
            return 1

        fpga_set_reg(CFG_DDR_SEL,"3")
        isbusy3 = (fpga_get_reg(DIAG_ST_CAS)&0x02) >> 1
        if(isbusy3 == 1):
            print("dimm 3 is busy!")
            return 1
    else:
        fpga_set_reg(CFG_DDR_SEL,dimm_str)
        isbusy = (fpga_get_reg(DIAG_ST_CAS)&0x02) >> 1
        if(isbusy == 1):
            print("dimm %s is busy!"%dimm_str)
            return 1

    return 0

    
def pa8910_ddr_diag_get_status(dimm_str):

    fpga_set_reg(CFG_DDR_SEL,dimm_str)
    dimm_status = fpga_get_reg(DIAG_ST_CAS)
    hpcii       = fpga_get_reg(DIAG_HPCII_READY)

    hpcii_ready = hpcii & 0x1
    ddr_busy    = ((dimm_status & 0x2) > 0)
    calib_success = ((hpcii & 0xe) == 0x6)
    if hpcii_ready > 0:
        hpcii_s = "ready"
    else:
        hpcii_s = "not ready"
    if ddr_busy > 0:
        ddr_s = "busy"
    else:
        ddr_s = "not busy"
    if calib_success > 0:
        calib_s = "success"
    else:
        calib_s = "fail"
    print("===============================")
    print("DDR           : %s" %dimm_str)
    print("diag_flag     : %d" %(dimm_status & 0x1))
    print("ddr_busy      : %s" %ddr_s)
    print("hpcii ready   : %s" %hpcii_s)
    print("calib_success : %s" %calib_s)



def pa8910_ddr_show_status(prog_name, argv):
    param_check(1, argv, show_usage, prog_name)

    dimm_str = argv.pop( 0 )

    if(dimm_str == "all"):
        pa8910_ddr_diag_get_status("0")
        pa8910_ddr_diag_get_status("1")
        pa8910_ddr_diag_get_status("2")
        pa8910_ddr_diag_get_status("3")
    elif(xint(dimm_str) <= 3):
        pa8910_ddr_diag_get_status(dimm_str)
    else:
        print(" dimm is illegal (%d), (dimm = 0,1,2,3,all)" % (xint(dimm_str)))
        show_usage( prog_name )
        sys.exit( -1 )

def get_error_counter(dimm):
    fpga_set_reg(CFG_DDR_SEL, dimm );
    ecl = fpga_get_reg(DIAG_ST_ECL)
    ech = fpga_get_reg(DIAG_ST_ECH)
    return ecl + ech*(2**16)

def get_wrdat_counter(dimm):
    fpga_set_reg(CFG_DDR_SEL, dimm );
    cntl = fpga_get_reg(DIAG_WRDAT_CNT_L)
    cnth = fpga_get_reg(DIAG_WRDAT_CNT_H)
    return cntl + cnth*(2**16)

def get_rddat_counter(dimm):
    fpga_set_reg(CFG_DDR_SEL, dimm );
    cntl = fpga_get_reg(DIAG_RDDAT_CNT_L)
    cnth = fpga_get_reg(DIAG_RDDAT_CNT_H)
    return cntl + cnth*(2**16)

def get_rdvld_counter(dimm):
    fpga_set_reg(CFG_DDR_SEL, dimm );
    cntl = fpga_get_reg(DIAG_RDVLD_CNT_L)
    cnth = fpga_get_reg(DIAG_RDVLD_CNT_H)
    return cntl + cnth*(2**16)

#return ms 
def _ddr_get_current_time():
    t = time.time()
    return int(round(t * 1000))

def _ddr_get_counter(val_str, dimm):
    if(val_str == "error"):
        cnt = get_error_counter(dimm) 
    elif(val_str == "wrdat"):
        cnt = get_wrdat_counter(dimm)
    elif(val_str == "rddat"):
        cnt = get_rddat_counter(dimm)
    elif(val_str == "rdvld"):
        cnt = get_rdvld_counter(dimm)
    else:
        return 0
    return cnt

def _get_rate_cnt(cnt_str,dimm):
    svalue = _ddr_get_counter(cnt_str,dimm)
    stv_time = _ddr_get_current_time()
    evalue = _ddr_get_counter(cnt_str,dimm)
    etv_time = _ddr_get_current_time()
    if(svalue > evalue):
        svalue = _ddr_get_counter(cnt_str,dimm)
        stv_time = _ddr_get_current_time()
        evalue = _ddr_get_counter(cnt_str,dimm)
        etv_time = _ddr_get_current_time()
    delta_ms = etv_time - stv_time
    rate = ( (evalue - svalue)*1000 ) / delta_ms
    counter = evalue
    return counter,rate



def _ddr_read_rate_cnt(dimm):
    cnt_name = ["error", "wrdat", "rddat", "rdvld"]
    print("===============================")
    print("DDR           : %s" %dimm)
    for cnt_str in cnt_name:
        counter,rate = _get_rate_cnt(cnt_str, dimm)
        print"%s count:%12d   rate:%10d "%(cnt_str, counter, rate)

def pa8910_ddr_show_rate(prog_name, argv):
    param_check(1, argv, show_usage, prog_name)

    dimm_str = argv.pop( 0 )
    if(dimm_str == "all"):
        _ddr_read_rate_cnt("0")
        _ddr_read_rate_cnt("1")
        _ddr_read_rate_cnt("2")
        _ddr_read_rate_cnt("3")
    elif(xint(dimm_str) <= 3):
        _ddr_read_rate_cnt(dimm_str)
    else:
        print(" dimm is illegal (%d), (dimm = 0,1,2,3,all)" % (xint(dimm_str)))
        show_usage( prog_name )
        sys.exit( -1 )

def pa8910_ddr_get_counter(dimm):
    global ddr_mode_type
    error_cnt = get_error_counter(dimm) 
    wrdat_cnt = get_wrdat_counter(dimm)
    rddat_cnt = get_rddat_counter(dimm)
    rdvld_cnt = get_rdvld_counter(dimm)
    print("===============================")
    print("DDR           : %s" %dimm)
    print("error         : %d" %error_cnt)
    print("rwdat         : %d" %wrdat_cnt)
    print("rddat         : %d" %rddat_cnt)
    print("rdvld         : %d" %rdvld_cnt)

    if ddr_mode_type == "1":
        return  wrdat_cnt == rddat_cnt
    else:
        return  int(error_cnt) == 0 and wrdat_cnt == rddat_cnt

def pa8910_ddr_show_counter(prog_name, argv):
    param_check(1, argv, show_usage, prog_name)

    dimm_str = argv.pop( 0 )
    if(dimm_str == "all"):
        result0 = pa8910_ddr_get_counter("0")
        result1 = pa8910_ddr_get_counter("1")
        result2 = pa8910_ddr_get_counter("2")
        result3 = pa8910_ddr_get_counter("3")
        return result0 == result1 == result2 == result3 == True
    elif(xint(dimm_str) <= 3):
        pa8910_ddr_get_counter(dimm_str)
    else:
        print(" dimm is illegal (%d), (dimm = 0,1,2,3,all)" % (xint(dimm_str)))
        show_usage( prog_name )
        sys.exit( -1 )


def fpga_ddr_set_addr(ddr_h, ddr_l):
    fpga_set_reg(DIAG_ADDR_H, ddr_h)
    fpga_set_reg(DIAG_ADDR_L, ddr_l)


def pa8910_ddr_write_paper( prog_name, argv ):
    param_check(3, argv, show_usage, prog_name)

    dimm_str  = argv.pop( 0 )
    ddr_h_str = argv.pop( 0 )
    ddr_l_str = argv.pop( 0 )
    if xint(dimm_str) > 3:
       print(" dimm is illegal (%d), (dimm = 0,1,2,3)" % (xint(dimm_str)))
       show_usage( prog_name )
       sys.exit( -1 ) 
    fpga_set_reg(CFG_DDR_SEL, dimm_str )
    fpga_ddr_set_addr( ddr_h_str, ddr_l_str )



def pa8910_ddr_api_write_data( prog_name, argv ):
    param_check(3, argv, show_usage, prog_name)

    dimm_str = argv.pop( 0 )
    addr_str = argv.pop( 0 )
    data_str = argv.pop( 0 )

    addr = xint(addr_str)
    data = xint(data_str)

    fpga_set_reg(CFG_DDR_SEL,dimm_str)
    fpga_set_reg(DIAG_ADDR_L, hex(addr&0xffff) )
    fpga_set_reg(DIAG_ADDR_H, hex( (addr>>16)&0xffff ) )

    for i in range(0, 36):
        fpga_set_reg(DIAG_DATA, hex(data&0xffff))
        fpga_set_reg(DIAG_DATA, hex( (data>>16)&0xffff ) )

    fpga_set_reg("0xb4a", "0x0001")

    for i in range(0, 10):
        value = fpga_get_reg("0xb4a")
        if (value&0x1) == 1:
            break
        time.sleep(0.01)

    if i >= 9:
        print("ddr write failed!")
        sys.exit( -1 )


def pa8910_ddr_api_read( prog_name, argv ):
    param_check(2, argv, show_usage, prog_name)

    dimm_str = argv.pop( 0 )
    addr_str = argv.pop( 0 )

    addr = xint(addr_str)

    fpga_set_reg(CFG_DDR_SEL,dimm_str)
    fpga_set_reg(DIAG_ADDR_L, hex(addr&0xffff) )
    fpga_set_reg(DIAG_ADDR_H, hex( (addr>>16)&0xffff ) )

    fpga_set_reg("0xb4a", "0x0001")

    for i in range(0, 10):
        value = fpga_get_reg("0xb4a")
        if (value&0x1) == 1:
            break
        time.sleep(0.01)

    if i >= 9:
        print("ddr read failed!")
        sys.exit( -1 )

    for i in range(0, 72):
        data = fpga_get_reg("0xb44")
        print("%d: %04x" %(i, data))


def pa8910_show_error_count( prog_name, argv ):
    param_check(2, argv, show_usage, prog_name)

    addr_str = argv.pop( 0 )
    dimm_str = argv.pop( 0 )
    
    fpga_set_reg(CFG_DDR_SEL,dimm_str)
    fpga_set_reg(DIAG_ST_EOF, addr_str)

    error_addr_l = fpga_get_reg(DIAG_ST_EAL)
    error_addr_h = fpga_get_reg(DIAG_ST_EAH)
    print("error addr: 0x%04x%04x" %(error_addr_h, error_addr_l))

    for i in range(0,72):
        data = fpga_get_reg(DIAG_ST_ED)
        print("%d: %04x" %(i, data))


# add by msj
def check_ddr_read_rate_cnt(dimm):
    cnt_name = ["error", "wrdat", "rddat", "rdvld"]
    print("===============================")
    print("DDR           : %s" %dimm)
    rate = -1
    flag = True
    for cnt_str in cnt_name:
        counter,rate = _get_rate_cnt(cnt_str, dimm)
        print"%s count:%12d   rate:%10d "%(cnt_str, counter, rate)
        if rate != 0:
            flag = False
            return flag
    return flag
        

def pa8910_ddr_check_rate():
    ddr_str_list = [str(_) for _ in range(4)]
    flag = True
    count = 0
    for dimm in ddr_str_list:
        count = 0
        while count < 20:
            flag = check_ddr_read_rate_cnt(dimm)
            if flag:
                break
            count += 1
            time.sleep(10)
        if count == 20:
            break      
    return flag

def test_ddr(name, burn_sleep_time=1):
    global ddr_mode_type
    filename = "/tmp/ddr_test_result"
    
    try:
        os.remove(filename)
    except OSError:
        pass
    
    burn_sleep_time = burn_sleep_time
    sleep_time = 15 if name == "l" else 80
    addr_str_list = [str(_) for _ in range(2)]
    mode_str_list = [str(_) for _ in range(8)]
    for addr in addr_str_list:
        ddr_mode_type = addr
        for mode in mode_str_list:
            if addr=="1" and mode == "4":
                continue
            if addr=="1"and mode =="5":
                continue
            print("*************{0} {1}*************".format(addr, mode))
            para_list = [addr, mode, "0", "all"]
            pa8910_ddr_diag_start(None, para_list)
            time.sleep(int(burn_sleep_time))
            stop_list = [addr, "all"]
            pa8910_ddr_diag_stop(None, stop_list)
            time.sleep(sleep_time)
            print("sleep_time: %d"%sleep_time)
            show_list = ["all"]
            pa8910_ddr_show_status(None, show_list)
            show_list = ["all"]
            result = pa8910_ddr_check_rate()
            
            if not result:
                with open(filename, "a+") as f:
                    f.write("FAIL\n")
                print("FAIL")
                return False
            if not pa8910_ddr_show_counter(None, show_list):
                with open(filename, "a+") as f:
                    f.write("FAIL\n")
                print("FAIL")
                return False
            with open(filename, "a+") as f:
                f.write("PASS\n")
    
    print("PASS")
    return 0
    """
    para_list = ["0", "1", "0", "all"]
    pa8910_ddr_diag_start(None, para_list)
    time.sleep(1)
    stop_list = ["0 ", "all"]
    time.sleep(1)
    show_list = ["all"]
    if not pa8910_ddr_show_counter(None, show_list)
        return False
    """
def test_ddr_prd(name):
    
    sleep_time = 15 if name == "l" else 80
    addr_str_list = ["0"]
    mode_str_list1 = ["5","6"]
    mode_str_list2 = ["0","1","2","3","6","7"]
    for addr in addr_str_list:
        if addr == "0":
            mode_str_list = mode_str_list1
        else:
            mode_str_list = mode_str_list2
        for mode in mode_str_list:
            print("*************{0} {1}*************".format(addr, mode))
            para_list = [addr, mode, "0", "all"]
            pa8910_ddr_diag_start(None, para_list)
            time.sleep(2)
            stop_list = [addr, "all"]
            pa8910_ddr_diag_stop(None, stop_list)
            time.sleep(sleep_time)
            show_list = ["all"]
            pa8910_ddr_show_status(None, show_list)
            show_list = ["all"]
            result = pa8910_ddr_check_rate()
            
            if not result:
                print("FAIL")
                return False
            if not pa8910_ddr_show_counter(None, show_list):
                print("FAIL")
                return False
    print("PASS")
    return 0

def test_ddr_start():
    addr_str_list = [str(_) for _ in range(2)]
    mode_str_list = [str(_) for _ in range(8)]
    for addr in addr_str_list:
        for mode in mode_str_list:
            print("*************{0} {1}*************".format(addr, mode))
            para_list = [addr, mode, "0", "all"]
            pa8910_ddr_diag_start(None, para_list)
            time.sleep(1)

def test_ddr_end_and_check(name):
    sleep_time = 7 if name == "low" else 70
    addr_str_list = [str(_) for _ in range(2)]
    mode_str_list = [str(_) for _ in range(8)]
    for addr in addr_str_list:
        stop_list = [addr, "all"]
        pa8910_ddr_diag_stop(None, stop_list)
        time.sleep(sleep_time)
        show_list = ["all"]
        pa8910_ddr_show_status(None, show_list)
        show_list = ["all"]
        if not pa8910_ddr_show_counter(None, show_list):
            print("FAIL")
            return False            
    print("PASS")
    return True

def pa8910_ddr_api_read( prog_name, argv ):
    param_check(2, argv, show_usage, prog_name)

    dimm_str = argv.pop( 0 )
    addr_str = argv.pop( 0 )

    addr = xint(addr_str)

    fpga_set_reg(CFG_DDR_SEL,dimm_str)
    fpga_set_reg(DIAG_ADDR_L, hex(addr&0xffff) )
    fpga_set_reg(DIAG_ADDR_H, hex( (addr>>16)&0xffff ) )

    fpga_set_reg("0xb4a", "0x0001")

    for i in range(0, 10):
        value = fpga_get_reg("0xb4a")
        if (value&0x1) == 1:
            break
        time.sleep(0.01)

    if i >= 9:
        print("ddr read failed!")
        sys.exit( -1 )

    for i in range(0, 72):
        data = fpga_get_reg("0xb44")
        print("%d: %04x" %(i, data))

def pa8910_ddr_api_write_data(prog_name, argv):
    param_check(3, argv, show_usage, prog_name)

    dimm_str = argv.pop( 0 )
    addr_str = argv.pop( 0 )
    data_str = argv.pop( 0 )

    addr = xint(addr_str)
    data = xint(data_str)

    fpga_set_reg(CFG_DDR_SEL,dimm_str)
    fpga_set_reg(DIAG_ADDR_L, hex(addr&0xffff) )
    fpga_set_reg(DIAG_ADDR_H, hex( (addr>>16)&0xffff ) )

    for i in range(0, 36):
        fpga_set_reg(DIAG_DATA, hex(data&0xffff))
        fpga_set_reg(DIAG_DATA, hex( (data>>16)&0xffff ) )

    fpga_set_reg("0xb4a", "0x0001")

    for i in range(0, 10):
        value = fpga_get_reg("0xb4a")
        if (value&0x1) == 1:
            break
        time.sleep(0.01)

    if i >= 9:
        print("ddr write failed!")
        sys.exit( -1 )

def main():
    prog_name = sys.argv.pop(0)
    if ( len(sys.argv) < 1 ):
        show_usage( prog_name )
        sys.exit( -1 )
    action = sys.argv.pop( 0 )
    if ( action == "start" ):
        pa8910_ddr_diag_start( prog_name, sys.argv )
    elif ( action == "stop" ):
        pa8910_ddr_diag_stop( prog_name, sys.argv )
    elif ( action == "show" ):
        name = sys.argv.pop( 0 )
        if name == "status":
            pa8910_ddr_show_status( prog_name, sys.argv )
        elif name == "counter":
            pa8910_ddr_show_counter( prog_name, sys.argv )
        elif name == "error":
            pa8910_show_error_count( prog_name, sys.argv )
        elif name == "rate":
            pa8910_ddr_show_rate( prog_name, sys.argv )
        else:
            show_usage( prog_name )
    elif ( action == "r" ):
        pa8910_ddr_api_read( prog_name, sys.argv )
    elif ( action == "w" ):
        pa8910_ddr_api_write_data( prog_name, sys.argv )
    elif ( action == "reset" ):
        pa8910_fpga_api_ddr_reset()    
    elif ( action == "diag" ):
        name = sys.argv.pop( 0 )
        sleep_time = sys.argv.pop( 0 )
        print(name, sleep_time)
        test_ddr(name, sleep_time)
    elif ( action == "diag_prd" ):
        name = sys.argv.pop( 0 )
        test_ddr_prd(name)
    elif ( action == "diag_start" ):
        test_ddr_start()
    elif ( action == "diag_stop" ):
        name = sys.argv.pop( 0 )
        test_ddr_end_and_check(name)
    else:
        show_usage( prog_name )
        sys.exit( -1 )

if __name__ == "__main__":
    main()



