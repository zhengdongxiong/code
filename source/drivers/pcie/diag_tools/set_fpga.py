#!/usr/bin/python
#!-*-coding:UTF8-*-
import os, sys

FILE_NAME="pa8910_util.py"
KEY_WORDS="I2C_DIAG = "


def show_usage( prog_name ):
    print("Usage:")
    print("     %s show" % prog_name)
    print("     %s <opt>" % prog_name)
    print("             <show>   : show current tool")
    print("             <opt>: 0->pcie-tool, 1->i2c-tool ")
    print("Example:")
    print("     %s show " % prog_name)
    print("     %s 0 " % prog_name)

def replace_file(filename, key_words, newline):
    #获取关键词所在行号
    cmd = "grep -n '%s' %s | awk -F: '{print $1}'"%(key_words, filename)
    line = os.popen(cmd).readlines()[0].replace( "\n", "" )

    #替换对应行号的内容
    cmd = "sed -i '%sc%s' %s"%(line, newline, filename)
    os.system(cmd)


def show_curent_id():
    cmd = "grep '%s' %s | awk '{print $3}' "%(KEY_WORDS, FILE_NAME)
    line = os.popen(cmd).readlines()[0].replace( "\n", "" )
    if int(line):
        print("Current use i2c-tool")
        return 0

    print("Current use pci-tool")
    return 0

def main():
    prog_name = sys.argv.pop(0)
    if ( len(sys.argv) != 1 ) :
        show_usage( prog_name )
        sys.exit( -1 )

    action = sys.argv.pop( 0 )
    if action=="show":
        show_curent_id()
        sys.exit(0)

    new_line = "%s%s"%(KEY_WORDS, action)
    replace_file(FILE_NAME, KEY_WORDS, new_line)
    sys.exit(0)
    
'''
    fpga_i2c_node = get_fpga_i2c_node(fpga_id)
    check_i2c_node(fpga_i2c_node)

    new_line = "%s\"%s\"\n"%(KEY_WORDS,fpga_i2c_node)
    replace_file(FILE_NAME, KEY_WORDS, new_line)
    show_curent_id()
    sys.exit(0)
'''

if __name__ == "__main__":
    main()


