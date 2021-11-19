#!/usr/bin/python
import os, sys
import struct
import time
import random


Version = "v0.1"
DEBUG_MODE = 0

'''
    PCIE (default)
'''
PCI_NODE="/dev/fpga-pa8910"
PCI_BAR="0"

'''
    I2C 
'''
I2C_DIAG = 0
I2C_NODE="/dev/i2c-pa8910"

LOG_FILENAME    = "/root/diag_log.txt"
RECORD_FILENAME = "/root/record.txt"
RECORD_FLAG     = 0
DEBUG_FLAG      = 0

def xint( r_str ):
    if "L" in r_str:
        r_str = r_str.replace("L","")
    if "x" in r_str:
        return int(r_str.replace( "\n", "" ),16)
    else:
        return int(r_str)


def dlog(msg):
    print("%s"%msg)
    if RECORD_FLAG:
        cmd_str = "echo %s >> %s"%(msg,LOG_FILENAME)
        os.system(cmd_str)


def record(msg):
    if RECORD_FLAG:
        cmd_str = "echo %s >> %s"%(msg,RECORD_FILENAME)
        os.system(cmd_str)


def debug(msg):
    if DEBUG_FLAG:
        print("[DEBUG:]" + msg)

def error_print(msg):
    print("     [ERROR]: %s"%msg)

def param_input_check(param_num, argv, usage, prog_name):
    if ( len(argv) != param_num ):
        usage( prog_name )
        sys.exit( -1 )

def Check_NODE():
    if I2C_DIAG:
        node = I2C_NODE
    else:
        node = PCI_NODE
        
    ret = os.path.exists(node)
    if ret==False:
        error_print("Can not find the Node %s !"%node)
        error_print("Please create the node first!" )
        sys.exit(-1)

def Check_Fpga_Device():
    if I2C_DIAG:
        cmd = "i2cgod -a %s -b 2 -d %s -O %s -r" %("0x30", I2C_NODE, "0x0")
    else:
        cmd = "fpgarw -b %s -a %s -r" %(PCI_BAR, "0x0")
        
    data_str = os.popen( cmd ).readlines()[0]
    if "error" in data_str:
        error_print("FPGA reg read error.")
        error_print("Can not find FPGA Device.")
        error_print("Please download fpga firmware first !")
        sys.exit(-1)
    return 0
    
'''
    PCIE TOOLS START
'''
class class_cpld_pci(object):
    def __init__(self):
        Check_NODE()
        Check_Fpga_Device()
        self.pci_bar = PCI_BAR

    def xset(self, addr, data ):
        data_set = hex(xint(data))
        pci_set_cmd = "fpgarw -b %s -a %s -w -v %s" %(self.pci_bar, addr, data_set)
        os.system( pci_set_cmd + " > /dev/null 2>&1")
        if DEBUG_MODE:
             print("[fpga] w %s %s"%(addr, data))

    def xget(self, addr ):
        pci_set_cmd = "fpgarw -b %s -a %s -r" %(self.pci_bar, addr)
        data = os.popen( pci_set_cmd ).readlines()[0].replace( "\n", "" )
        if DEBUG_MODE:
             print("[fpga] r %s (%s)"%(addr,data))
        return xint(data) & 0xffff


class class_fpga_pci(object):
    def __init__(self):
        Check_NODE()
        Check_Fpga_Device()
        self.pci_bar = PCI_BAR

    def xset(self, addr, data ):
        data_set = hex(xint(data))
        pci_set_cmd = "fpgarw -b %s -a %s -w -v %s" %(self.pci_bar, addr, data_set)
        os.system( pci_set_cmd + " > /dev/null 2>&1")
        if DEBUG_MODE:
             print("[fpga] w %s %s"%(addr, data))

    def xget(self, addr ):
        pci_set_cmd = "fpgarw -b %s -a %s -r" %(self.pci_bar, addr)
        data = os.popen( pci_set_cmd ).readlines()[0].replace( "\n", "" )
        if DEBUG_MODE:
             print("[fpga] r %s (%s)"%(addr,data))
        return xint(data) & 0xffff
'''
    PCIE TOOLS END
'''

'''
    I2C TOOLS START
'''
def get_pa8910_bus():
    bus_str = os.popen( "readlink %s"%I2C_NODE ).readlines()[0]
    bus_num = os.path.basename(bus_str.replace( "\n", "" ) )
    bus_num = bus_num.replace("i2c-","")
    return bus_num

def Check_Cpld_Device():
    i2c_read_cmd = "i2cget -f -y %s %s %s"%(get_pa8910_bus(), "0x20", "0x0")
    data_str = os.popen( i2c_read_cmd ).readlines()[0]
    if "Error" in data_str:
        error_print("Can not find CPLD i2c Device.")
        sys.exit(-1)
    return 0

class class_cpld_i2c(object):
    def __init__(self):
        Check_NODE()
        Check_Cpld_Device()
        self.bus = get_pa8910_bus()
        self.addr= "0x20"

    def xset(self, addr, data ):
        data_str = hex(data)
        i2c_set_cmd = "i2cset -y -f %s %s %s %s"%(self.bus, self.addr, addr, data_str) 
        os.system( i2c_set_cmd + " > /dev/null 2>&1" )
        if DEBUG_MODE:
            print("[cpld] w %s %s"%(addr, data_str))


    def xget(self, addr ):
        i2c_read_cmd = "i2cget -f -y %s %s %s"%(self.bus, self.addr, addr)
        data_str = os.popen( i2c_read_cmd ).readlines()[0]
        if DEBUG_MODE:
            print("[cpld] r %s (%s)"%(addr, hex(xint(data_str) & 0xff)))
        return xint(data_str) & 0xff


class class_fpga_i2c(object):
    def __init__(self):
        Check_NODE()
        Check_Fpga_Device()
        self.i2c_dev = I2C_NODE
        self.dev_addr = "0x30"

    def xset(self, addr, data ):
        data_l = hex(xint(data) & 0xff)
        data_h = hex((xint(data)>>8) & 0xff)
        i2c_set_cmd = "i2cgod -a %s -d %s -w -b 2 -O %s %s %s" %(self.dev_addr, self.i2c_dev, addr, data_l, data_h)
        os.system( i2c_set_cmd + " > /dev/null 2>&1")
        if DEBUG_MODE:
             print("[fpga] w %s %s"%(addr, data))

    def xget(self, addr ):
        i2c_read_cmd = "i2cgod -a %s -b 2 -d %s -O %s -r" %(self.dev_addr, self.i2c_dev, addr)
        data_str = os.popen( i2c_read_cmd ).readlines()[0]
        data = "0x"+data_str[4:6]+data_str[1:3]
        if DEBUG_MODE:
             print("[fpga] r %s (%s)"%(addr,data))
        return xint(data) & 0xffff

'''
    I2C TOOLS END
'''
