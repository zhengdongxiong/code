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

RA_DEV_ID     = "0x000"
RA_DEV_SUBID  = "0x002"
RA_REV_MAJOR  = "0x004"
RA_REV_MINOR  = "0x006"
RA_BUILD_YEAR = "0x008"
RA_BUILD_DATE = "0x00a"
RA_BUILD_TIME = "0x00c"
RA_TEST_SLB   = "0x00e"
RA_TEST_READ  = "0x010"
RA_SOFT_RESET = "0x080"


def show_usage( prog_name ):
    prog_name=os.path.basename(prog_name)
    print("Usage:")
    print("     ./%s reset" % prog_name)
    print("     ./%s show version" %prog_name)
    print("     ./%s w <addr_16> <data_16>" %prog_name)
    print("     ./%s r <addr_16>" %prog_name)
    print("Example:")
    print("     ./%s reset " % prog_name)
    print("     ./%s show version" %prog_name)
    print("     ./%s w 0x0234 0x4321" %prog_name)
    print("     ./%s r 0x0234" %prog_name)



def pa8910_fpga_api_init():
    fpga_set_reg(RA_SOFT_RESET,"0xffff")
    time.sleep(1)
    fpga_set_reg(RA_SOFT_RESET,"0x0")
    print("FPGA init success!")
    return 0
    
def fm1100_fpga_api_show_version():
    device_id = hex(fpga_get_reg(RA_DEV_ID))
    dev_subid = hex(fpga_get_reg(RA_DEV_SUBID))
    dev_major = hex(fpga_get_reg(RA_REV_MAJOR))
    dev_minor = hex(fpga_get_reg(RA_REV_MINOR))
    year      = hex(fpga_get_reg(RA_BUILD_YEAR))
    date      = hex(fpga_get_reg(RA_BUILD_DATE))
    time      = hex(fpga_get_reg(RA_BUILD_TIME))
    print("===============================")
    print("FPGA INFO:")
    print("     device id   : %s" %device_id[2:])
    print("     dev sub id  : %s" %dev_subid[2:])
    print("     dev major   : %s" %dev_major[2:])
    print("     dev minor   : %s" %dev_minor[2:])
    print("     build year  : %s" %year[2:])
    print("     build date  : %s" %date[2:])
    print("     build time  : %s" %time[2:])
    return 0

def pa8910_fpga_api_write_reg( prog_name, argv ):
    param_check(2, argv, show_usage, prog_name)

    addr = argv.pop( 0 )
    data = argv.pop( 0 )
    fpga_set_reg(addr, data)

    return 0

def pa8910_fpga_api_read_reg( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    addr = argv.pop( 0 )
    data = fpga_get_reg(addr) 
    print("0x%04x"%data)
    return 0

def main():
    prog_name = sys.argv.pop(0)
    if ( len(sys.argv) < 1 ) :
        show_usage( prog_name )
        sys.exit( -1 )
    action = sys.argv.pop( 0 )
    if ( action == "reset" ):
        pa8910_fpga_api_init()
    elif( action == "show"):
        name = sys.argv.pop( 0 )
        if ( name == "version" ):
            fm1100_fpga_api_show_version()
        else:
           show_usage( prog_name )
    elif( action == "w"):
        pa8910_fpga_api_write_reg( prog_name, sys.argv )
    elif( action == "r"):
        pa8910_fpga_api_read_reg( prog_name, sys.argv )
    else:
        show_usage( prog_name )
    sys.exit( -1 )


if __name__ == "__main__":
    main()

