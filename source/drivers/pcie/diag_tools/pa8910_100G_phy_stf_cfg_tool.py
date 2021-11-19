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


def phy_write_reg(lane, addr, data):
    data_l = hex( data & 0xFFFF )
    data_h = hex( (data >> 16) & 0xFFFF )
    ilane = xint(lane)
    
    fpga_set_reg("0xe0e", addr )
    fpga_set_reg("0xe0e", hex(ilane<<3) )
    
    fpga_set_reg("0xe12", data_h )
    fpga_set_reg("0xe10", data_l )

    for i in range(10):
        time.sleep(0.01)
        value = fpga_get_reg("0xe14")
        if (value&0x1) == 0:
            break

    if(value&0x1) != 0:
        print("read error! %s: %s"%(RECONFIG_RNW, hex(value)))
        sys.exit( -1 )

    fpga_set_reg("0xe14", "0")


def phy_read_reg(lane, addr):
    ilane = xint(lane)
    
    fpga_set_reg("0xe0e", addr)
    fpga_set_reg("0xe0e", hex(ilane<<3))
    
    for i in range(10):
        time.sleep(0.01)
        value = fpga_get_reg("0xe14")
        if (value&0x1) == 0:
            break

    if(value&0x1) != 0:
        print("read error! %s: %s"%(RECONFIG_RNW, hex(value)))
        sys.exit( -1 )

    fpga_set_reg("0xe14", "1")
    dataL = fpga_get_reg( "0xe16" )
    dataH = fpga_get_reg( "0xe18" )
    return ( dataL + dataH*(2**16) )

    

# LANE Loop Enable
def lane_loop_enable(lane):
    pass_flag = 0
    phy_write_reg(lane, "0x84", "0x1")
    phy_write_reg(lane, "0x85", "0x1")
    phy_write_reg(lane, "0x86", "0x08")
    phy_write_reg(lane, "0x87", "0x0")
    phy_write_reg(lane, "0x90", "0x1")

    for i in range(10):
        time.sleep(0.001)
        val = phy_read_reg(lane, "0x8a")
        if (val & 0x80):
            pass_flag = 1
            break
     
    if pass_flag == 0:
        #print("lane %s loop enable failed !"%lane)
        return 1

    pass_flag = 0
    for i in range(10):
        time.sleep(0.001)
        val = phy_read_reg(lane, "0x8b")
        if (val & 0x1) == 0:
            pass_flag = 1
            break
    
    if pass_flag == 0:
        #print("lane %s loop enable failed !"%lane)
        return 1
            
    phy_write_reg(lane, "0x8a", "0x80")
    
    return 0

#LANE Initail Adaptation
def lane_adaptation_init(lane):
    pass_flag = 0
    phy_write_reg(lane, "0x84", "0x1")
    phy_write_reg(lane, "0x85", "0x0")
    phy_write_reg(lane, "0x86", "0x0a")
    phy_write_reg(lane, "0x87", "0x0")
    phy_write_reg(lane, "0x90", "0x1")

    for i in range(10):
        time.sleep(0.001)
        val = phy_read_reg(lane, "0x8a")
        if (val & 0x80):
            pass_flag = 1
            break
     
    if pass_flag == 0:
        #print("lane %s loop enable failed !"%lane)
        return 1

    pass_flag = 0
    for i in range(10):
        time.sleep(0.001)
        val = phy_read_reg(lane, "0x8b")
        if (val & 0x1) == 0:
            pass_flag = 1
            break
    
    if pass_flag == 0:
        #print("lane %s loop enable failed !"%lane)
        return 1
            
    phy_write_reg(lane, "0x8a", "0x80")
    
    return 0

#LANE Read Status
def lane_read_status(lane):
    pass_flag = 0
    phy_write_reg(lane, "0x84", "0x0")
    phy_write_reg(lane, "0x85", "0xb")
    phy_write_reg(lane, "0x86", "0x26")
    phy_write_reg(lane, "0x87", "0x1")
    phy_write_reg(lane, "0x90", "0x1")
    return 0


#LANE Loop Disable
def lane_loop_disable(lane):
    pass_flag = 0
    phy_write_reg(lane, "0x84", "0x0")
    phy_write_reg(lane, "0x85", "0x1")
    phy_write_reg(lane, "0x86", "0x08")
    phy_write_reg(lane, "0x87", "0x0")
    phy_write_reg(lane, "0x90", "0x1")

    for i in range(10):
        time.sleep(0.001)
        val = phy_read_reg(lane, "0x8a")
        if (val & 0x80):
            pass_flag = 1
            break
     
    if pass_flag == 0:
        #print("lane %s loop enable failed !"%lane)
        return 1

    pass_flag = 0
    for i in range(10):
        time.sleep(0.001)
        val = phy_read_reg(lane, "0x8b")
        if (val & 0x1) == 0:
            pass_flag = 1
            break
    
    if pass_flag == 0:
    #print("lane %s loop enable failed !"%lane)
        return 1
            
    phy_write_reg(lane, "0x8a", "0x80")
    
    return 0

#############
# 命令行
#############
#./mx2100_100G_phy_stf_cfg_tool.py {CHN}
#CHN:通道号0-11
def api_phy_100G_reg_config(channel):
    fpga_set_reg("0xe00", channel)
    #step 1
    lane_loop_enable("0")
    lane_loop_enable("1")
    lane_loop_enable("2")
    lane_loop_enable("3")
    #step 2
    lane_adaptation_init("0")
    lane_adaptation_init("1")
    lane_adaptation_init("2")
    lane_adaptation_init("3")
    #step 3
    lane_read_status("0")
    lane_read_status("1")
    lane_read_status("2")
    lane_read_status("3")
    #step 4
    lane_loop_disable("0")
    lane_loop_disable("1")
    lane_loop_disable("2")
    lane_loop_disable("3")
    #step 5
    lane_adaptation_init("0")
    lane_adaptation_init("1")
    lane_adaptation_init("2")
    lane_adaptation_init("3")
    #step 6/7
    for i in range(2):
        lane_read_status("0")
        lane_read_status("1")
        lane_read_status("2")
        lane_read_status("3")
        
    return 0
    

def show_usage( prog_name ):
    prog_name=os.path.basename(prog_name)
    print("====================================")
    print("Version : %s" %Version)
    print("Usage:")
    print("     ./%s <channel> " % prog_name)
    print("         <channel>: 0~11")


def pa8910_fpga_api_100G_phy_reg_config( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel = argv.pop( 0 )

    api_phy_100G_reg_config(channel)


 
def main():
    prog_name = sys.argv.pop(0)
    if ( len(sys.argv) < 1 ) :
        show_usage( prog_name )
        sys.exit( -1 )

    pa8910_fpga_api_100G_phy_reg_config( prog_name, sys.argv )


if __name__ == "__main__":
    main()

