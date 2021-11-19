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


MODULE_SEL      = "0xe00"
STATUS_ADDR     = "0xe02"
STATUS_WDAT_L   = "0xe04"
STATUS_WDAT_H   = "0xe06"
STATUS_RNW      = "0xe08"
STATUS_RDAT_L   = "0xe0a"
STATUS_RDAT_H   = "0xe0c"
RECONFIG_ADDR   = "0xe0e"
RECONFIG_WDAT_L = "0xe10"
RECONFIG_WDAT_H = "0xe12"
RECONFIG_RNW    = "0xe14"
RECONFIG_RDAT_L = "0xe16"
RECONFIG_RDAT_H = "0xe18"
STATUS          = "0xe1A"
CTRL            = "0xe1C"

# Tx reg
GEN_MODULE_SEL = "0xe40"
GEN_OFF        = "0xe42"
GEN_DAT        = "0xe44"
GEN_CAS        = "0xe46"
GEN_MAX        = "0xe48"
GEN_MIN        = "0xe4a"
GEN_LOOP       = "0xe4c"
GEN_CNT        = "0xe4e"
GEN_GAP        = "0xe50"
GEN_STOP       = "0xe52"
GEN_SOP_L32_L = "0xe54"
GEN_SOP_L32_H = "0xe56"
GEN_SOP_H32_L = "0xe58"
GEN_SOP_H32_H = "0xe5a"
GEN_PKT_L32_L = "0xe5c"
GEN_PKT_L32_H = "0xe5e"
GEN_PKT_H32_L = "0xe60"
GEN_PKT_H32_H = "0xe62"
GEN_BYT_L32_L = "0xe64"
GEN_BYT_L32_H = "0xe66"
GEN_BYT_H32_L = "0xe68"
GEN_BYT_H32_H = "0xe6a"

# rx reg
CAP_MODULE_SEL = "0xe80"
CAP_CAS        = "0xe82"
CAP_STT        = "0xe84"
CAP_PSZ        = "0xe86"
CAP_DAT        = "0xe88"
CAP_OFF        = "0xe8a"
CAP_SOP_L32_L  = "0xe8c"
CAP_SOP_L32_H  = "0xe8e"
CAP_SOP_H32_L  = "0xe90"
CAP_SOP_H32_H  = "0xe92"
CAP_PKT_L32_L  = "0xe94"
CAP_PKT_L32_H  = "0xe96"
CAP_PKT_H32_L  = "0xe98"
CAP_PKT_H32_H  = "0xe9a"
CAP_ERR_L32_L  = "0xe9c"
CAP_ERR_L32_H  = "0xe9e"
CAP_ERR_H32_L  = "0xea0"
CAP_ERR_H32_H  = "0xea2"
CAP_BYTE_L32_L = "0xea4"
CAP_BYTE_L32_H = "0xea6"
CAP_BYTE_H32_L = "0xea8"
CAP_BYTE_H32_H = "0xeaa"

#=======================GLOBE DEFINE=======================
GEN_RAM_OFFSET_DEFAULT = 0x0000
CAP_CAS_DEFAULT        = 0x0001
CAP_STT_DEFAULT        = 0x0001   


GEN_CAS_ENDLESS        = 0x000f
GEN_CAS_LIMITED        = 0x000b
GEN_CAS_DEFAULT        = 0x0101
GEN_CAS_STOP           = 0x0009

PKT_MAX_LEN             = 1518
PKT_MIN_LEN             = 60
REG16_MAX               = 65535
READ_TRY_CNT            = 10

WRITEN_DATA = [ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 ]
WRITEN_DATA[0]  = ["0000","0C07","AC51","0010","DBFF","2070","0800","4500","008F","E30E","0000","FD11","CA3B","0102","0304","0506",\
                   "0708","03FF","0400","007B","F027","0001","0203","0405","0607","0809","0A0B","0C0D","0E0F","1011","1213","1415"]
WRITEN_DATA[1]  = ["1617","1819","1A1B","1C1D","1E1F","2021","2223","2425","2627","2829","2A2B","2C2D","2E2F","3031","3233","3435",\
                   "3637","3839","3A3B","3C3D","3E3F","4041","4243","4445","4647","4849","4A4B","4C4D","4E4F","5051","5253","5455"]
WRITEN_DATA[2]  = ["5657","5859","5A5B","5C5D","5E5F","6061","6263","6465","6667","6869","6A6B","6C6D","6E6F","7071","7273","7475",\
                   "7677","7879","7A7B","7C7D","7E7F","8081","8283","8485","8687","8889","8A8B","8C8D","8E8F","9091","9293","9495"]
WRITEN_DATA[3]  = ["9697","9899","9A9B","9C9D","9E9F","A0A1","A2A3","A4A5","A6A7","A8A9","AAAB","ACAD","AEAF","B0B1","B2B3","B4B5",\
                   "B6B7","B8B9","BABB","BCBD","BEBF","C0C1","C2C3","C4C5","C6C7","C8C9","CACB","CCCD","CECF","D0D1","D2D3","D4D5"]
WRITEN_DATA[4]  = ["D6D7","D8D9","DADB","DCDD","DEDF","E0E1","E2E3","E4E5","E6E7","E8E9","EAEB","ECED","EEEF","F0F1","F2F3","F4F5",\
                   "F6F7","F8F9","FAFB","FCFD","FEFF","0001","0203","0405","0607","0809","0A0B","0C0D","0E0F","1011","1213","1415"]
WRITEN_DATA[5]  = ["1617","1819","1A1B","1C1D","1E1F","2021","2223","2425","2627","2829","2A2B","2C2D","2E2F","3031","3233","3435",\
                   "3637","3839","3A3B","3C3D","3E3F","4041","4243","4445","4647","4849","4A4B","4C4D","4E4F","5051","5253","5455"]
WRITEN_DATA[6]  = ["5657","5859","5A5B","5C5D","5E5F","6061","6263","6465","6667","6869","6A6B","6C6D","6E6F","7071","7273","7475",\
                   "7677","7879","7A7B","7C7D","7E7F","8081","8283","8485","8687","8889","8A8B","8C8D","8E8F","9091","9293","9495"]
WRITEN_DATA[7]  = ["9697","9899","9A9B","9C9D","9E9F","A0A1","A2A3","A4A5","A6A7","A8A9","AAAB","ACAD","AEAF","B0B1","B2B3","B4B5",\
                   "B6B7","B8B9","BABB","BCBD","BEBF","C0C1","C2C3","C4C5","C6C7","C8C9","CACB","CCCD","CECF","D0D1","D2D3","D4D5"]
WRITEN_DATA[8]  = ["D6D7","D8D9","DADB","DCDD","DEDF","E0E1","E2E3","E4E5","E6E7","E8E9","EAEB","ECED","EEEF","F0F1","F2F3","F4F5",\
                   "F6F7","F8F9","FAFB","FCFD","FEFF","0001","0203","0405","0607","0809","0A0B","0C0D","0E0F","1011","1213","1415"]
WRITEN_DATA[9]  = ["1617","1819","1A1B","1C1D","1E1F","2021","2223","2425","2627","2829","2A2B","2C2D","2E2F","3031","3233","3435",\
                   "3637","3839","3A3B","3C3D","3E3F","4041","4243","4445","4647","4849","4A4B","4C4D","4E4F","5051","5253","5455"]
WRITEN_DATA[10] = ["5657","5859","5A5B","5C5D","5E5F","6061","6263","6465","6667","6869","6A6B","6C6D","6E6F","7071","7273","7475",\
                   "7677","7879","7A7B","7C7D","7E7F","8081","8283","8485","8687","8889","8A8B","8C8D","8E8F","9091","9293","9495"]
WRITEN_DATA[11] = ["9697","9899","9A9B","9C9D","9E9F","A0A1","A2A3","A4A5","A6A7","A8A9","AAAB","ACAD","AEAF","B0B1","B2B3","B4B5",\
                   "B6B7","B8B9","BABB","BCBD","BEBF","C0C1","C2C3","C4C5","C6C7","C8C9","CACB","CCCD","CECF","D0D1","D2D3","D4D5"]
WRITEN_DATA[12] = ["D6D7","D8D9","DADB","DCDD","DEDF","E0E1","E2E3","E4E5","E6E7","E8E9","EAEB","ECED","EEEF","F0F1","F2F3","F4F5",\
                   "F6F7","F8F9","FAFB","FCFD","FEFF","0001","0203","0405","0607","0809","0A0B","0C0D","0E0F","1011","1213","1415"]
WRITEN_DATA[13] = ["1617","1819","1A1B","1C1D","1E1F","2021","2223","2425","2627","2829","2A2B","2C2D","2E2F","3031","3233","3435",\
                   "3637","3839","3A3B","3C3D","3E3F","4041","4243","4445","4647","4849","4A4B","4C4D","4E4F","5051","5253","5455"]
WRITEN_DATA[14] = ["5657","5859","5A5B","5C5D","5E5F","6061","6263","6465","6667","6869","6A6B","6C6D","6E6F","7071","7273","7475",\
                   "7677","7879","7A7B","7C7D","7E7F","8081","8283","8485","8687","8889","8A8B","8C8D","8E8F","9091","9293","9495"]
WRITEN_DATA[15] = ["9697","9899","9A9B","9C9D","9E9F","A0A1","A2A3","A4A5","A6A7","A8A9","AAAB","ACAD","AEAF","B0B1","B2B3","B4B5",\
                   "B6B7","B8B9","BABB","BCBD","BEBF","C0C1","C2C3","C4C5","C6C7","C8C9","CACB","CCCD","CECF","D0D1","D2D3","D4D5"]
WRITEN_DATA[16] = ["D6D7","D8D9","DADB","DCDD","DEDF","E0E1","E2E3","E4E5","E6E7","E8E9","EAEB","ECED","EEEF","F0F1","F2F3","F4F5",\
                   "F6F7","F8F9","FAFB","FCFD","FEFF","0001","0203","0405","0607","0809","0A0B","0C0D","0E0F","1011","1213","1415"]
WRITEN_DATA[17] = ["1617","1819","1A1B","1C1D","1E1F","2021","2223","2425","2627","2829","2A2B","2C2D","2E2F","3031","3233","3435",\
                   "3637","3839","3A3B","3C3D","3E3F","4041","4243","4445","4647","4849","4A4B","4C4D","4E4F","5051","5253","5455"]
WRITEN_DATA[18] = ["5657","5859","5A5B","5C5D","5E5F","6061","6263","6465","6667","6869","6A6B","6C6D","6E6F","7071","7273","7475",\
                   "7677","7879","7A7B","7C7D","7E7F","8081","8283","8485","8687","8889","8A8B","8C8D","8E8F","9091","9293","9495"]
WRITEN_DATA[19] = ["9697","9899","9A9B","9C9D","9E9F","A0A1","A2A3","A4A5","A6A7","A8A9","AAAB","ACAD","AEAF","B0B1","B2B3","B4B5",\
                   "B6B7","B8B9","BABB","BCBD","BEBF","C0C1","C2C3","C4C5","C6C7","C8C9","CACB","CCCD","CECF","D0D1","D2D3","D4D5"]
WRITEN_DATA[20] = ["D6D7","D8D9","DADB","DCDD","DEDF","E0E1","E2E3","E4E5","E6E7","E8E9","EAEB","ECED","EEEF","F0F1","F2F3","F4F5",\
                   "F6F7","F8F9","FAFB","FCFD","FEFF","0001","0203","0405","0607","0809","0A0B","0C0D","0E0F","1011","1213","1415"]
WRITEN_DATA[21] = ["1617","1819","1A1B","1C1D","1E1F","2021","2223","2425","2627","2829","2A2B","2C2D","2E2F","3031","3233","3435",\
                   "3637","3839","3A3B","3C3D","3E3F","4041","4243","4445","4647","4849","4A4B","4C4D","4E4F","5051","5253","5455"]
WRITEN_DATA[22] = ["5657","5859","5A5B","5C5D","5E5F","6061","6263","6465","6667","6869","6A6B","6C6D","6E6F","7071","7273","7475",\
                   "7677","7879","7A7B","7C7D","7E7F","8081","8283","8485","8687","8889","8A8B","8C8D","8E8F","9091","9293","9495"]
WRITEN_DATA[23] = ["9697","9899","9A9B","9C9D","9E9F","A0A1","A2A3","A4A5","A6A7","A8A9","AAAB","ACAD","AEAF","B0B1","B2B3","B4B5",\
                   "B6B7","B8B9","BABB","BCBD","BEBF","411A","9DEF","0000","0000","0000","0000","0000","0000","0000","0000","0000"]

#100G
def show_usage( prog_name ):
    prog_name=os.path.basename(prog_name)
    print("====================================")
    print("Version : %s" %Version)
    print("Usage:")
    print("     ./%s init <channel_id>" % prog_name)
    print("     ./%s start <channel_id> <min_len> <max_len> <fixed_mode> <loop> <gap> " % prog_name     )
    print("                 <channel_id> : (0,1,2,3)  ")
    print("                 <min_len>    : (60<=  min_len < 1518,  min_len < max_len)")
    print("                 <max_len>    : (60<= max_len <=1518, min_len < max_len)")
    print("                 <fixed_mode> : (0: packet length not fixed, 1:fixed)")
    print("                 <loop>       : (0: endless  other: loop times)")
    print("                 <gap>        : (0< gap <65536)")
    print("     ./%s stop  <channel_id> " % prog_name)
    print("     ./%s show  <txrx/interface/counter/cgb/background/fifo/stats> <channel_id> " % prog_name)
    print("     ./%s r <mac/phy> <channel_id> <addr> " % prog_name)
    print("     ./%s w <mac/phy> <channel_id> <addr> <data> " % prog_name)
    print("     ./%s clear <channel_id>" % prog_name)
    print("     ./%s reset" % prog_name)
    print("     ./%s open_bk <channel_id> " % prog_name)
    print("     ./%s close_bk <channel_id> " % prog_name)
    print("     ./%s powerup_cgb <channel_id> " % prog_name)
    print("Example:")
    print("     ./%s init 1" % prog_name)
    print("     ./%s start 1 64 1024 0 1 " % prog_name)
    print("     ./%s stop 1" % prog_name)
    print("     ./%s show interface 1" % prog_name)
    print("     ./%s show txrx 1" % prog_name)
    print("     ./%s r mac 1 0x0135" % prog_name)
    print("     ./%s w phy 1 0x0214 0x0001 0x0123" % prog_name)
    print("     ./%s clear 1" % prog_name)
    print("     ./%s reset" % prog_name)



#=======================BASE API=======================
def eth100_channel_set(etype, channel):
    if etype not in ["tx", "rx", "mac"]:
        print("UnKnow sel type : %s"%etype )
        sys.exit(-1)

    # if (xint(channel) > 3):
    #     print("channel is out of range should be:[0,1,2,3] (%s)"%channel )
    #     sys.exit(-1)

    if(etype == "tx"):
        fpga_set_reg(GEN_MODULE_SEL, channel )
    elif(etype == "rx"):
        fpga_set_reg(CAP_MODULE_SEL, channel )
    else:
        fpga_set_reg(MODULE_SEL, channel )


def set_gen_ram_content( ):
    for i in range( 0, 24 ):
        fpga_set_reg(GEN_OFF, hex(i) )  #set offset
        for val in WRITEN_DATA[i]:
            fpga_set_reg( GEN_DAT, "0x"+val )   #set data ,32 times


def pa8910_fpga_api_100g_start(prog_name, argv):
    param_check(6, argv, show_usage, prog_name)

    channel_id      = argv.pop( 0 )
    min_len         = argv.pop( 0 )
    max_len         = argv.pop( 0 )
    fixed_mode      = argv.pop( 0 )
    loop            = argv.pop( 0 )
    gap             = argv.pop( 0 )

    eth100_channel_set('tx', channel_id)
    # fpga_set_reg(GEN_STOP, "0x0")
    fpga_set_reg(GEN_MIN, min_len )
    fpga_set_reg(GEN_MAX, max_len )
    fpga_set_reg(GEN_GAP, gap )


    if  xint(loop) == 0 : # endless mode 
        if(fixed_mode == "0"):  #not fixed mode
            fpga_set_reg(GEN_LOOP, "0x1" )  # can"t be zero, required by FPGA department
            fpga_set_reg(GEN_CAS, "0x5" )  # 0xf
        else: #fixed mode
            fpga_set_reg(GEN_LOOP, "0x1" )  # can"t be zero, required by FPGA department
            fpga_set_reg(GEN_CAS, "0xd" )  # 0xf
    else :    # limited mode 
        if(fixed_mode == "0"):  #not fixed mode
            fpga_set_reg(GEN_LOOP, loop )
            fpga_set_reg(GEN_CAS, "0x1" )  # 0xf
        else: #fixed mode
            fpga_set_reg(GEN_LOOP, loop )
            fpga_set_reg(GEN_CAS, "0x9" )  # 0xf
    
    return 0

def pa8910_fpga_api_100g_stop(prog_name, argv):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )

    eth100_channel_set('tx', channel_id)
    fpga_set_reg(GEN_STOP, "1")
    time.sleep(0.1)
    fpga_set_reg(GEN_STOP, "0")

 
def pa8910_fpga_api_100G_show_status(prog_name, argv):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )

    eth100_channel_set('tx', channel_id)

    tmp = [ 0, 0, 0, 0]
    tmp[0] = fpga_get_reg(GEN_SOP_L32_L)
    tmp[1] = fpga_get_reg(GEN_SOP_L32_H)
    tmp[2] = fpga_get_reg(GEN_SOP_H32_L) 
    tmp[3] = fpga_get_reg(GEN_SOP_H32_H)
    Sop_Val = tmp[0] + (tmp[1]<<16) + (tmp[2]<<32)+ (tmp[3]<<48)

    # fpga_set_reg(GEN_MODULE_SEL, channel_id )
    tmp[0] = fpga_get_reg(GEN_PKT_L32_L)
    tmp[1] = fpga_get_reg(GEN_PKT_L32_H)
    tmp[2] = fpga_get_reg(GEN_PKT_H32_L)
    tmp[3] = fpga_get_reg(GEN_PKT_H32_H)  
    PktCnt_Val = tmp[0] + (tmp[1]<<16) + (tmp[2]<<32)+ (tmp[3]<<48)

    # fpga_set_reg(GEN_MODULE_SEL, channel_id )
    tmp[0] = fpga_get_reg(GEN_BYT_L32_L)
    tmp[1] = fpga_get_reg(GEN_BYT_L32_H)
    tmp[2] = fpga_get_reg(GEN_BYT_H32_L)  
    tmp[3] = fpga_get_reg(GEN_BYT_H32_H)
    Byte_Val = tmp[0] + (tmp[1]<<16) + (tmp[2]<<32)+ (tmp[3]<<48)

    print("===============================")
    print("channel: %s "%(channel_id))
    print("Tx status:")
    print("          Sop:    %d" % (Sop_Val))
    print("          PktCnt: %d" % (PktCnt_Val))
    print("          Byte:   %d" % (Byte_Val))
    tmp_PktCnt_Val = PktCnt_Val

    eth100_channel_set("rx", channel_id)

    tmp[0] = fpga_get_reg(CAP_SOP_L32_L)
    tmp[1] = fpga_get_reg(CAP_SOP_L32_H)
    tmp[2] = fpga_get_reg(CAP_SOP_H32_L) 
    tmp[3] = fpga_get_reg(CAP_SOP_H32_H)
    Sop_Val = tmp[0] + (tmp[1]<<16) + (tmp[2]<<32)+ (tmp[3]<<48)

    tmp[0] = fpga_get_reg(CAP_PKT_L32_L)
    tmp[1] = fpga_get_reg(CAP_PKT_L32_H)
    tmp[2] = fpga_get_reg(CAP_PKT_H32_L) 
    tmp[3] = fpga_get_reg(CAP_PKT_H32_H)
    PktCnt_Val = tmp[0] + (tmp[1]<<16) + (tmp[2]<<32)+ (tmp[3]<<48)

    tmp[0] = fpga_get_reg(CAP_ERR_L32_L)
    tmp[1] = fpga_get_reg(CAP_ERR_L32_H)
    tmp[2] = fpga_get_reg(CAP_ERR_H32_L) 
    tmp[3] = fpga_get_reg(CAP_ERR_H32_H)
    ErrCnt_Val = tmp[0] + (tmp[1]<<16) + (tmp[2]<<32)+ (tmp[3]<<48)

    tmp[0] = fpga_get_reg(CAP_BYTE_L32_L)
    tmp[1] = fpga_get_reg(CAP_BYTE_L32_H)
    tmp[2] = fpga_get_reg(CAP_BYTE_H32_L) 
    tmp[3] = fpga_get_reg(CAP_BYTE_H32_H)
    Byte_Val = tmp[0] + (tmp[1]<<16) + (tmp[2]<<32)+ (tmp[3]<<48)
    print("===============================")
    print("channel: %s "%(channel_id))
    print("Rx status:")
    print("          Sop:    %d" % (Sop_Val))
    print("          PktCnt: %d" % (PktCnt_Val))
    print("          ErrCnt: %d" % (ErrCnt_Val))
    print("          Byte:   %d" % (Byte_Val))
    return PktCnt_Val == tmp_PktCnt_Val and PktCnt_Val != 0, PktCnt_Val


def pa8910_fpga_api_100g_show_interface_status( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )

    eth100_channel_set("mac", channel_id)

    status = fpga_get_reg(STATUS)

    if (status&0xf) == 0xf:
        status_str = "linkup"
    else:
        status_str = "down" 
    print("===============================")
    print("channel: %s "%(channel_id))
    print("100G port status:")
    print("          port_linkup     : %s" % (status_str))
    print("          TX_LANES_STABLE : %d" % (status&0x8 > 0))
    print("          RX_PCS_READY    : %d" % (status&0x4 > 0))
    print("          RX_BLOCK_LOCK   : %d" % (status&0x2 > 0))
    print("          RX_AM_LOCK      : %d" % (status&0x1 > 0))


def phy_read_reg(channel, lane, addr):
    ilane = xint(lane)
    fpga_set_reg(MODULE_SEL, channel)
    
    fpga_set_reg(RECONFIG_ADDR, addr)
    fpga_set_reg(RECONFIG_ADDR, hex(ilane<<3))
    
    for i in range(10):
        time.sleep(0.01)
        value = fpga_get_reg(RECONFIG_RNW)
        if (value&0x1) == 0:
            break

    if(value&0x1) != 0:
        print("read error! %s: %s"%(RECONFIG_RNW, hex(value)))
        sys.exit( -1 )

    fpga_set_reg(RECONFIG_RNW,"1")
    dataL = fpga_get_reg( RECONFIG_RDAT_L )
    dataH = fpga_get_reg( RECONFIG_RDAT_H )
    return ( dataL + dataH*(2**16) )
    
def phy_write_reg(channel, lane, addr, data):
    data_l = hex( data & 0xFFFF )
    data_h = hex( (data >> 16) & 0xFFFF )
    ilane = xint(lane)
    
    fpga_set_reg(MODULE_SEL, channel)
    
    fpga_set_reg(RECONFIG_ADDR, addr )
    fpga_set_reg(RECONFIG_ADDR, hex(ilane<<3) )
    
    fpga_set_reg(RECONFIG_WDAT_H, data_h )
    fpga_set_reg(RECONFIG_WDAT_L, data_l )

    for i in range(10):
        time.sleep(0.01)
        value = fpga_get_reg(RECONFIG_RNW)
        if (value&0x1) == 0:
            break

    if(value&0x1) != 0:
        print("read error! %s: %s"%(RECONFIG_RNW, hex(value)))
        sys.exit( -1 )

    fpga_set_reg(RECONFIG_RNW,"0")

def pa8910_fpga_api_100G_phy_read( prog_name, argv ):
    param_check(3, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    lane       = argv.pop( 0 )
    phy_addr_str = argv.pop( 0 )
    
    data = phy_read_reg(channel_id, lane, phy_addr_str)
    print("0x%08x" %data)


def pa8910_fpga_api_100G_phy_write( prog_name, argv ):
    param_check(4, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    lane       = argv.pop( 0 )
    phy_addr_str = argv.pop( 0 )
    data_str = argv.pop( 0 )

    phy_write_reg(channel_id, lane, phy_addr_str, xint(data_str))


def pa8910_fpga_api_avl_read(prog_name, argv):
    param_check(2, argv, show_usage, prog_name)

    channel_id  = argv.pop( 0 )    
    addr_str    = argv.pop( 0 )
    value = tse_avl_mm_read(channel_id, addr_str)
    print("0x%08x" %value)


def pa8910_fpga_api_avl_write(prog_name, argv):
    param_check(3, argv, show_usage, prog_name)

    channel_id  = argv.pop( 0 )
    addr_str    = argv.pop( 0 )
    data_str    = argv.pop( 0 )

    tse_avl_mm_write(channel_id, addr_str, xint(data_str))

def tse_avl_mm_read(channel_str, addr):
    eth100_channel_set("mac", channel_str)

    fpga_set_reg(RECONFIG_ADDR, addr )

    for i in range(10):
        time.sleep(0.01)
        value = fpga_get_reg(RECONFIG_RNW)
        if (value&0x1) == 0:
            break

    if(value&0x1) != 0:
        print("read error! %s: %s"%(RECONFIG_RNW, hex(value)))
        sys.exit( -1 )

    fpga_set_reg(RECONFIG_RNW,"1")
    dataL = fpga_get_reg( RECONFIG_RDAT_L )
    dataH = fpga_get_reg( RECONFIG_RDAT_H )
    return ( dataL + dataH*(2**16) )



def tse_avl_mm_write(channel_str, addr , data):
    data_l = hex( data & 0xFFFF )
    data_h = hex( (data >> 16) & 0xFFFF )
    eth100_channel_set("mac", channel_str)
    fpga_set_reg(RECONFIG_ADDR, addr )
    fpga_set_reg(RECONFIG_WDAT_H, data_h )
    fpga_set_reg(RECONFIG_WDAT_L, data_l )

    for i in range(10):
        time.sleep(0.01)
        value = fpga_get_reg(RECONFIG_RNW)
        if (value&0x1) == 0:
            break

    if(value&0x1) != 0:
        print("read error! %s: %s"%(RECONFIG_RNW, hex(value)))
        sys.exit( -1 )

    fpga_set_reg(RECONFIG_RNW,"0")


def mac_mm_read(channel_str, addr):
    eth100_channel_set("mac", channel_str)
    fpga_set_reg(CTRL, "0x8000" )
    fpga_set_reg(STATUS_ADDR, addr )
    fpga_set_reg(STATUS_RNW, "1" )
    dataL = fpga_get_reg( STATUS_RDAT_L )
    dataH = fpga_get_reg( STATUS_RDAT_H )
    fpga_set_reg(STATUS_RNW, "0" )
    return ( dataL + dataH*(2**16) )

def mac_mm_write(channel_str, addr, data):
    eth100_channel_set("mac", channel_str)

    data_l = hex( data & 0xFFFF )
    data_h = hex( (data >> 16) & 0xFFFF )

    fpga_set_reg(STATUS_ADDR,addr)
    fpga_set_reg(STATUS_WDAT_H, data_h )
    fpga_set_reg(STATUS_WDAT_L, data_l )
    fpga_set_reg(STATUS_RNW, "0" )




def pa8910_fpga_api_100G_mac_read( prog_name, argv ):
    param_check(2, argv, show_usage, prog_name)
    channel_id  = argv.pop( 0 )    
    addr_str    = argv.pop( 0 )

    data = mac_mm_read(channel_id, addr_str)
    print("0x%08x" %data)


def pa8910_fpga_api_100G_mac_write( prog_name, argv ):
    param_check(3, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    phy_addr_str = argv.pop( 0 )
    data_str = argv.pop( 0 )

    mac_mm_write(channel_id, phy_addr_str, xint(data_str))
 

def clear_count(s_channel):
    #TX clear
    eth100_channel_set('tx', s_channel)
    fpga_set_reg(GEN_CAS, "0x100")
    fpga_set_reg(GEN_CAS, "0x000")
    #RX clear
    eth100_channel_set("rx", s_channel)
    fpga_set_reg(CAP_CAS, "0x1")
    fpga_set_reg(CAP_CAS, "0x0")

def pa8910_fpga_api_clear_count( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    clear_count(channel_id)


def pa8910_fpga_api_100G_init( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )

    eth100_channel_set('tx', channel_id)

    set_gen_ram_content()




def _eth_100G_init(channel):
    tse_avl_mm_write(channel, "0x92", 0x12d0 )       #link timer
    tse_avl_mm_write(channel, "0x93", 0x13 )         #link timer
    tse_avl_mm_write(channel, "0x94", 0x00 )         #if_mode = 0x0000. 1000BASE-X/SGMII PCS is default in 1000BASE-X Mode, SGMII_ENA = 0, USE_SGMII_AN = 0
    tse_avl_mm_write(channel, "0x80", 0x0140 )       #PCS Control Register: Disable Auto Negotiation
    tse_avl_mm_write(channel, "0x80", 0x8140 )       #PCS Reset
    for i in range(0, READ_TRY_CNT):
        time.sleep(0.1)
        value = tse_avl_mm_read(channel, "0x80")     
        if(value&0x8000 == 0):
            break
        
    if(value&0x8000 != 0):
        print("tse avl mm is busy")
        sys.exit( -1 )

    tse_avl_mm_write(channel, "0x02", 0x00800220 )    #Command_config Register = 0x00800220
    tse_avl_mm_write(channel, "0x09", 2032 )          #Tx_section_empty = Max FIFO size - 16
    tse_avl_mm_write(channel, "0x0e", 3 )             #Tx_almost_full = 3                   
    tse_avl_mm_write(channel, "0x0d", 8 )             #Tx_almost_empty = 8                  
    tse_avl_mm_write(channel, "0x07", 2032 )          #Rx_section_empty = Max FIFO size - 16
    tse_avl_mm_write(channel, "0x0c", 8 )             #Rx_almost_full = 8                   
    tse_avl_mm_write(channel, "0x0b", 8 )             #Rx_almost_empty = 8                  
    tse_avl_mm_write(channel, "0x0a", 16 )            #Tx_section_full = 16                 
    tse_avl_mm_write(channel, "0x08", 16 )            #Rx_section_full = 16                 
    tse_avl_mm_write(channel, "0x03", 0x17231C00 )    #mac_0 = 0x17231C00
    tse_avl_mm_write(channel, "0x04", 0x0000CB4A )    #mac_1 = 0x0000CB4A
    tse_avl_mm_write(channel, "0x05", 1518 )          #Frm_length = 1518                   
    tse_avl_mm_write(channel, "0x17", 12 )            #Tx_ipg_length = 12                  
    tse_avl_mm_write(channel, "0x06", 0xffff )        #Pause_quant = 0xFFFF                
    tse_avl_mm_write(channel, "0x02", 0x00800220 )    #Command_config Register = 0x00800220
    tse_avl_mm_write(channel, "0x02", 0x00802220 )    #Set SW_RESET bit to 1
    value = tse_avl_mm_read(channel, "0x02")          
    for i in range(0, READ_TRY_CNT):
        time.sleep(0.1)
        value = tse_avl_mm_read(channel, "0x80")                                   
        if( (value&0x2000) == 0):
            break
    if( (value&0x2000) != 0):
        print("tse avl mm is busy")
        sys.exit( -1 )

    tse_avl_mm_write(channel, "0x02", 0x0080023b )    #Set TX_ENA and RX_ENA to 1 in Command Config Register PROMIS_EN=1  ETH_SPEED=1


def pa8910_fpga_api_100G_reset():
    fpga_set_reg("0x80", "0x1f00")
    time.sleep(0.01)
    fpga_set_reg("0x80", "0")
    print("100G port reset success!")


def _get_64bit_count(channel, addr):
    addr_l = hex(addr)
    addr_h = hex(addr + 1)
    data_l = mac_mm_read(channel, addr_l)
    data_h = mac_mm_read(channel, addr_h)
    return data_l + (data_h << 32)

def pa8910_fpga_api_100G_show_ip_counter( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel = argv.pop( 0 )

    print("====================================")
    print("100G IP TX MAC COUNTERS (channel: %s):" %channel)
    print("<64Byte and crc_err            :%ld"%(_get_64bit_count(channel, 0x0800)))
    print("oversized and crc_err          :%ld"%(_get_64bit_count(channel, 0x0802)))
    print("transmit pkt and FCS_err       :%ld"%(_get_64bit_count(channel, 0x0804)))
    print(">=64Byte and FCS_err           :%ld"%(_get_64bit_count(channel, 0x0806)))
    print("64 Byte frame transmit         :%ld"%(_get_64bit_count(channel, 0x0816)))
    print("65-127 Byte frame transmit     :%ld"%(_get_64bit_count(channel, 0x0818)))
    print("128-255 Byte frame transmit    :%ld"%(_get_64bit_count(channel, 0x081a)))
    print("256-511 Byte frame transmit    :%ld"%(_get_64bit_count(channel, 0x081c)))
    print("512-1023 Byte frame transmit   :%ld"%(_get_64bit_count(channel, 0x081e)))
    print("1024-1518 Byte frame transmit  :%ld"%(_get_64bit_count(channel, 0x0820)))
    print(">=1519 Byte frame transmit     :%ld"%(_get_64bit_count(channel, 0x0822)))
    print("oversized Byte frame transmit  :%ld"%(_get_64bit_count(channel, 0x0824)))
    print("runt pkt(9~64 Byte) transmit   :%ld"%(_get_64bit_count(channel, 0x0834)))
    print("payloadOctets OK counter       :%ld"%(_get_64bit_count(channel, 0x0860)))
    print("frameloadOctets OK counter     :%ld"%(_get_64bit_count(channel, 0x0862)))
    print("====================================")
    print("100G IP RX MAC COUNTERS (channel: %s):" %channel)
    print("<64Byte and crc_err(64it)      :%ld"%(_get_64bit_count(channel, 0x0900)))
    print("oversized and crc_err(64it)    :%ld"%(_get_64bit_count(channel, 0x0902)))
    print("transmit pkt and FCS_err(64it) :%ld"%(_get_64bit_count(channel, 0x0904)))
    print(">=64Byte and FCS_err(64it)     :%ld"%(_get_64bit_count(channel, 0x0906)))
    print("64 Byte frame transmit         :%ld"%(_get_64bit_count(channel, 0x0916)))
    print("65-127 Byte frame transmit     :%ld"%(_get_64bit_count(channel, 0x0918)))
    print("128-255 Byte frame transmit    :%ld"%(_get_64bit_count(channel, 0x091a)))
    print("256-511 Byte frame transmit    :%ld"%(_get_64bit_count(channel, 0x091c)))
    print("512-1023 Byte frame transmit   :%ld"%(_get_64bit_count(channel, 0x091e)))
    print("1024-1518 Byte frame transmit  :%ld"%(_get_64bit_count(channel, 0x0920)))
    print(">=1519 Byte frame transmit     :%ld"%(_get_64bit_count(channel, 0x0922)))
    print("oversized Byte frame transmit  :%ld"%(_get_64bit_count(channel, 0x0924)))
    print("runt pkt(9~64 Byte) transmit   :%ld"%(_get_64bit_count(channel, 0x0934)))
    print("payloadOctets OK counter       :%ld"%(_get_64bit_count(channel, 0x0960)))
    print("frameloadOctets OK counter     :%ld"%(_get_64bit_count(channel, 0x0962)))
    print("====================================")
    print("100G PSC MESSAGE (channel: %s):" %channel)
    print("word lock                      :%d"%( mac_mm_read(channel, "0x0312"))   )
    print("FIFO status                    :%d"%( mac_mm_read(channel, "0x0314"))   )
    print("freq lock                      :%d"%( mac_mm_read(channel, "0x0321"))   )
    print("core_status                    :%d"%( mac_mm_read(channel, "0x0322"))   )
    print("virtual lane frame error       :%d"%( mac_mm_read(channel, "0x0323"))   )
    print("sclr frame error               :%d"%( mac_mm_read(channel, "0x0324"))   )
    print("AM lock                        :%d"%( mac_mm_read(channel, "0x0328"))   )
    print("PCS_Vlane0                     :%d"%( mac_mm_read(channel, "0x0330"))   )
    print("PCS_Vlane1                     :%d"%( mac_mm_read(channel, "0x0331"))   )
    print("PCS_Vlane2                     :%d"%( mac_mm_read(channel, "0x0332"))   )
    print("PCS_Vlane3                     :%d"%( mac_mm_read(channel, "0x0333"))   )
    print("REF_CLK0                       :%d"%( mac_mm_read(channel, "0x0340"))   )
    print("REF_CLK1                       :%d"%( mac_mm_read(channel, "0x0341"))   )
    print("REF_CLK2                       :%d"%( mac_mm_read(channel, "0x0342"))   )


def pa8910_fpga_api_show_background_stats( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    data_542  = tse_avl_mm_read(channel_id, "0x542")
    data_d42  = tse_avl_mm_read(channel_id, "0xd42")
    data_1542 = tse_avl_mm_read(channel_id, "0x1542")
    data_1d42 = tse_avl_mm_read(channel_id, "0x1d42")
    print("====================================")
    print("100G background state (channel: %s):" %channel_id)
    print("reg 0x542  : 0x%x  "%(data_542))
    print("reg 0xd42  : 0x%x  "%(data_d42))
    print("reg 0x1542 : 0x%x  "%(data_1542))
    print("reg 0x1d42 : 0x%x  "%(data_1d42))

def _100G_background_set(channel, data):
    tse_avl_mm_write(channel, "0x542", data )
    tse_avl_mm_write(channel, "0xd42", data )
    tse_avl_mm_write(channel, "0x1542", data )
    tse_avl_mm_write(channel, "0x1d42", data )


def pa8910_fpga_api_close_background( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    _100G_background_set(channel_id, 0x0)

def pa8910_fpga_api_open_background( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    _100G_background_set(channel_id, 0x1)


def pa8910_fpga_api_100G_read_cgb( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    data_112 = tse_avl_mm_read(channel_id, "0x112")
    data_912 = tse_avl_mm_read(channel_id, "0x912")
    data_1112 = tse_avl_mm_read(channel_id, "0x1112")
    data_1912 = tse_avl_mm_read(channel_id, "0x1912")
    print("====================================")
    print("100G CGB state (channel: %s):" %channel_id)
    print("reg 0x0112 : 0x%x  "%(data_112))
    print("reg 0x0912 : 0x%x  "%(data_912))
    print("reg 0x1112 : 0x%x  "%(data_1112))
    print("reg 0x1912 : 0x%x  "%(data_1912))


def pa8910_fpga_api_100G_powerup_cgb( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    tse_avl_mm_write(channel_id, "0x112", 0x23 )
    tse_avl_mm_write(channel_id, "0x912", 0x23 )
    tse_avl_mm_write(channel_id, "0x1112", 0x23 )
    tse_avl_mm_write(channel_id, "0x1912", 0x23 )


def pa8910_fpga_api_show_0x100_to_0x180( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    print("====================================")
    print("0x100 to 0x180 (channel: %s):" %channel_id)
    for i in range(0x100, 0x181):
        print("reg 0x%04x : 0x%x  "%( i, tse_avl_mm_read(channel_id, hex(i)) ))

    print("====================================")
    print("0x900 to 0x980 (channel: %s):" %channel_id)
    for i in range(0x900, 0x981):
        print("reg 0x%04x : 0x%x  "%( i, tse_avl_mm_read(channel_id, hex(i)) ))

    print("====================================")
    print("0x1100 to 0x1180 (channel: %s):" %channel_id)
    for i in range(0x1100, 0x1181):
        print("reg 0x%04x : 0x%x  "%( i, tse_avl_mm_read(channel_id, hex(i)) ))

    print("====================================")
    print("0x1900 to 0x1980 (channel: %s):" %channel_id)
    for i in range(0x1900, 0x1981):
        print("reg 0x%04x : 0x%x  "%( i, tse_avl_mm_read(channel_id, hex(i)) ))


def pa8910_fpga_api_show_fifo_stats( prog_name, argv ):
    param_check(1, argv, show_usage, prog_name)

    channel_id = argv.pop( 0 )
    mac_mm_write(channel_id, "0x0314", 0x0)
    data_1 = mac_mm_read(channel_id, "0x0315")
    mac_mm_write(channel_id, "0x0314", 0x1)
    data_2 = mac_mm_read(channel_id, "0x0315")
    print("====================================")
    print("fifo status (channel: %s):" %channel_id)
    print("0x0315_1 : 0x%x"%data_1)
    print("0x0315_2 : 0x%x"%data_2)

def pa8910_fpga_diag_100G():
    filename = "/tmp/fpga_100g.txt"
    channel_id_list = [str(_) for _ in range(4)]
    # backgroud

    try:
        os.remove(filename)
    except OSError:
        pass

    print("backgroud")
    for _ in range(2):
        for channel in channel_id_list:
            pa8910_fpga_api_close_background(None, [channel])
    
    print("powe up cgb")
    # powe up cgb
    for _ in range(2):
        for channel in channel_id_list:
            pa8910_fpga_api_100G_powerup_cgb(None, [channel])

    print("init")
    # init
    for channel in channel_id_list:
        pa8910_fpga_api_100G_init(None, [channel])

    print("send packet")
    # send packet
    for channel in channel_id_list:
        para_list = [channel, "60", "60", "0", "0", "10"]
        pa8910_fpga_api_100g_start(None, para_list)
    time.sleep(2)

    print("stop")
    # stop
    for channel in channel_id_list:
        pa8910_fpga_api_100g_stop(None, [channel])

    print("show")
    # show
    for channel in channel_id_list:
        result, pkt = pa8910_fpga_api_100G_show_status(None, [channel])
        if not result:
            print("FAIL")
            return -1
    
        with open(filename, "a+") as f:
            f.write(str(pkt)+"\n")

    print("PASS")
    return 0


def load_serdes_params():
    print("====load 100G serdes params====")
    for channel in ["0","1","2","3"]:
        #lane 0
        tse_avl_mm_write(channel, "0x105", 0x40)
        tse_avl_mm_write(channel, "0x107", 0x82)
        tse_avl_mm_write(channel, "0x109", 0xf8)
        #lane 1
        tse_avl_mm_write(channel, "0x905", 0x40)
        tse_avl_mm_write(channel, "0x907", 0x82)
        tse_avl_mm_write(channel, "0x909", 0xf8)
        #lane 2
        tse_avl_mm_write(channel, "0x1105", 0x40)
        tse_avl_mm_write(channel, "0x1107", 0x82)
        tse_avl_mm_write(channel, "0x1109", 0xf8)
        #lane 3
        tse_avl_mm_write(channel, "0x1905", 0x40)
        tse_avl_mm_write(channel, "0x1907", 0x82)
        tse_avl_mm_write(channel, "0x1909", 0xf8)



def pa8910_fpga_diag_100G_start():
    channel_id_list = [str(_) for _ in range(4)]
    # backgroud

    print("backgroud")
    for _ in range(2):
        for channel in channel_id_list:
            pa8910_fpga_api_close_background(None, [channel])
    
    print("powe up cgb")
    # powe up cgb
    for _ in range(2):
        for channel in channel_id_list:
            pa8910_fpga_api_100G_powerup_cgb(None, [channel])

    print("init")
    # init
    for channel in channel_id_list:
        pa8910_fpga_api_100G_init(None, [channel])

    print("send packet")
    # send packet
    for channel in channel_id_list:
        para_list = [channel, "60", "60", "0", "0", "10"]
        pa8910_fpga_api_100g_start(None, para_list)
    time.sleep(2)

def pa8910_fpga_diag_100G_end_and_check():

    filename = "/tmp/fpga_100g.txt"
    channel_id_list = [str(_) for _ in range(4)]
    # backgroud

    try:
        os.remove(filename)
    except OSError:
        pass

    print("stop")
    # stop
    for channel in channel_id_list:
        pa8910_fpga_api_100g_stop(None, [channel])
        time.sleep(3)

    print("show")
    # show
    for channel in channel_id_list:
        result, pkt = pa8910_fpga_api_100G_show_status(None, [channel])
        if not result:
            print("FAIL")
            return -1
    
        with open(filename, "a+") as f:
            f.write(str(pkt)+"\n")

    print("PASS")
    return 0
    
def rsfec_reg_read(addr):
    fpga_set_reg("0x0e28", addr )
    fpga_set_reg("0x0e2c","0x1") 
    
    pass_flag = 0
    for i in range(10):
        time.sleep(0.001)
        value = fpga_get_reg("0xe2c")
        if value == 0:
            pass_flag = 1
            break
            
    if pass_flag == 0:
        print("read counter failed!")
        return 1
    
    value = fpga_get_reg("0x0e2e")
    return value&0xff

def pa8910_rsfec_reg_read( prog_name, argv ):
    param_check(2, argv, show_usage, prog_name)

    channel = argv.pop( 0 )
    addr = argv.pop( 0 )

    fpga_set_reg(MODULE_SEL, channel)
    value = rsfec_reg_read(addr)
    print("0x%02x"%value)


def rsfec_reg_write(addr, data):
    fpga_set_reg("0x0e28", addr)
    fpga_set_reg("0x0e2a", data)
    fpga_set_reg("0x0e2c","0x0")
    for i in range(10):
        time.sleep(0.001)
        value = fpga_get_reg("0xe2c")
        if value == 0:
            return 0
    print("rsfec write failed!")
    return 1


def pa8910_rsfec_reg_write( prog_name, argv ):
    param_check(3, argv, show_usage, prog_name)

    channel = argv.pop( 0 )
    addr = argv.pop( 0 )
    data = argv.pop( 0 )

    fpga_set_reg(MODULE_SEL, channel)
    rsfec_reg_write(addr, data)

    
def main():
    prog_name = sys.argv.pop(0)
    if ( len(sys.argv) < 1 ) :
        show_usage( prog_name )
        sys.exit( -1 )
    action = sys.argv.pop( 0 )
    if ( action == "start" ):
        pa8910_fpga_api_100g_start( prog_name, sys.argv )
    elif ( action == "stop" ):
        pa8910_fpga_api_100g_stop( prog_name, sys.argv )
    elif ( action == "init"):
        pa8910_fpga_api_100G_init( prog_name, sys.argv )
    elif ( action == "show"):
        name = sys.argv.pop( 0 )
        if name == "txrx":
            pa8910_fpga_api_100G_show_status( prog_name, sys.argv )    
        elif name == "interface":
            pa8910_fpga_api_100g_show_interface_status( prog_name, sys.argv )
        elif name == "counter":
            pa8910_fpga_api_100G_show_ip_counter( prog_name, sys.argv )
        elif (name == "cgb"):
            pa8910_fpga_api_100G_read_cgb( prog_name, sys.argv )
        elif (name == "background"):
            pa8910_fpga_api_show_background_stats( prog_name, sys.argv )
        elif (name == "stats"):
            pa8910_fpga_api_show_0x100_to_0x180( prog_name, sys.argv )
        elif (name == "fifo"):
            pa8910_fpga_api_show_fifo_stats( prog_name, sys.argv )
    elif ( action == "r"):
        dev = sys.argv.pop( 0 )
        if ( dev == "mac"):
            pa8910_fpga_api_100G_mac_read( prog_name, sys.argv )
        elif (dev == "phy"):
            pa8910_fpga_api_100G_phy_read( prog_name, sys.argv )
        elif (dev == "rsfec"):
            pa8910_rsfec_reg_read( prog_name, sys.argv )    
        else :
            show_usage( prog_name )
    elif ( action == "w"):
        dev = sys.argv.pop( 0 )
        if ( dev == "mac"):
            pa8910_fpga_api_100G_mac_write( prog_name, sys.argv )
        elif (dev == "phy"):
            pa8910_fpga_api_100G_phy_write( prog_name, sys.argv )
        elif (dev == "rsfec"):
            pa8910_rsfec_reg_write( prog_name, sys.argv )    
        else :
            show_usage( prog_name )
    elif ( action == "clear" ):
        pa8910_fpga_api_clear_count(prog_name, sys.argv)
    elif ( action == "reset"):
        pa8910_fpga_api_100G_reset()
    elif ( action == "close_bk"):
        pa8910_fpga_api_close_background(prog_name, sys.argv)
    elif ( action == "open_bk"):
        pa8910_fpga_api_open_background(prog_name, sys.argv)
    elif ( action == "powerup_cgb"):
        pa8910_fpga_api_100G_powerup_cgb(prog_name, sys.argv)
    elif ( action == "diag" ):
        pa8910_fpga_diag_100G()
    elif ( action == "diag_start"):
        pa8910_fpga_diag_100G_start()
    elif ( action == "diag_stop"):
        pa8910_fpga_diag_100G_end_and_check()
    else:
        show_usage( prog_name )
        sys.exit( -1 )


if __name__ == "__main__":
    main()
