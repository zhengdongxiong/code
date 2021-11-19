#!/bin/bash


function show_usage()
{
    echo "Usage:"
    echo "  $1 {ACTION} {MODE} {CHN}"
    echo "      ACTION : close / open "
    echo "      MODE   : loop  / exter"
    echo "      CHN    : 0~11         "
    echo "Example:"
    echo "  $1 open  loop 0" 
    echo "  $1 close loop 0"
}

ACTION=$1
MODE=$2
CHN=$3


#TOOL_100_PY="./net.sh"
#TOOL_100_STF_PY="./net.sh"
TOOL_100_PY="./pa8910_100G_packet_tool.py"
TOOL_100_STF_PY="./pa8910_100G_phy_stf_cfg_tool.py"

if [ $# -ne 3 ];then
    show_usage $0
    exit 1
fi

if [ $MODE != "loop" ] && [ $MODE != "exter" ];then
    show_usage $0
    exit 3
fi

if [ $CHN -lt 0 ] || [ $CHN -gt 11 ];then
    show_usage $0
    exit 4
fi

test -e dr_switch.sh          || { echo "Not Found dr_switch.sh";         exit 5; }
test -e ${TOOL_100_PY}        || { echo "Not Found ${TOOL_100_PY}";     exit 6; }
test -e ${TOOL_100_STF_PY}    || { echo "Not Found ${TOOL_100_STF_PY}"; exit 7; }
#test -e ${ACTION}.patch       || { echo "Not Found ${ACTION}.patch";      exit 8; }


function action_colse_open()
{
    #disable_serdes
    echo "---------------- disable_serdes ----------------"
    for lane in `seq 0 3`
    do
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0084 0x00
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0085 0x00
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0086 0x01
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0087 0x00
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0090 0x01
        ${TOOL_100_PY} r phy ${CHN} $lane 0x008a
        ${TOOL_100_PY} r phy ${CHN} $lane 0x008b
        ${TOOL_100_PY} w phy ${CHN} $lane 0x008a 0x80
    done
    
    #tx_rx_soft_reset_hold
    echo "---------------- tx_rx_soft_reset_hold ----------------"
    ${TOOL_100_PY} w mac ${CHN} 0x310 0x6
    
    #pma_4ch_reset
    echo "---------------- pma_4ch_reset ----------------"
    for lane in `seq 0 3`
    do
        ${TOOL_100_PY} w phy ${CHN} $lane 0x203 0x81
    done
    
    #restart_pma_sequencer
    echo "---------------- restart_pma_sequencer ----------------"
    for lane in `seq 0 3`
    do
        ${TOOL_100_PY} w phy ${CHN} $lane 0x91 0x1
    done
    
    #dr_switch
    echo "---------------- dr_switch ----------------"
    source dr_switch.sh
    
    #enable_serdes
    echo "---------------- enable_serdes ----------------"
    for lane in `seq 0 3`
    do
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0084 0x07
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0085 0x00
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0086 0x01
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0087 0x00
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0090 0x01
        ${TOOL_100_PY} r phy ${CHN} $lane 0x008a
        ${TOOL_100_PY} r phy ${CHN} $lane 0x008b
        ${TOOL_100_PY} w phy ${CHN} $lane 0x008a 0x80
    done
    
    #dr_reset
    echo "---------------- dr_reset ----------------"
    ${TOOL_100_PY} w mac ${CHN} 0x00e 0x8
    ${TOOL_100_PY} w mac ${CHN} 0x00e 0xc
    ${TOOL_100_PY} w mac ${CHN} 0x00e 0xe
    ${TOOL_100_PY} w mac ${CHN} 0x00e 0xf
    ${TOOL_100_PY} w mac ${CHN} 0x00e 0xe
    ${TOOL_100_PY} w mac ${CHN} 0x00e 0xc
    ${TOOL_100_PY} w mac ${CHN} 0x00e 0x8
    ${TOOL_100_PY} w mac ${CHN} 0x00e 0x0
    
    #soft_rx_reset_hold
    echo "---------------- soft_rx_reset_hold ----------------"
    ${TOOL_100_PY} w mac ${CHN} 0x310 0x4
}

function mode_exter()
{
    ${TOOL_100_STF_PY} ${CHN}
}

function mode_loop()
{
    # Step1 —— Loop Enable
    echo "---------------- Step1 —— Loop Enable ----------------"
    for lane in `seq 0 3`
    do
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0084 0x01
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0085 0x01
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0086 0x08
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0087 0x00
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0090 0x01
        ${TOOL_100_PY} r phy ${CHN} $lane 0x008a
        ${TOOL_100_PY} r phy ${CHN} $lane 0x008b
        ${TOOL_100_PY} w phy ${CHN} $lane 0x008a 0x80
    done
    
    # Step2 —— Initail Adaptation
    echo "---------------- Initail Adaptation ----------------"
    for lane in `seq 0 3`
    do
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0084 0x01
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0085 0x00
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0086 0x0a 
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0087 0x00
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0090 0x01
        ${TOOL_100_PY} r phy ${CHN} $lane 0x008a
        ${TOOL_100_PY} r phy ${CHN} $lane 0x008b
        ${TOOL_100_PY} w phy ${CHN} $lane 0x008a 0x80
    done
    
    # Step3 —— Read Status
    echo "---------------- Step3 —— Read Status ----------------"
    for lane in `seq 0 3`
    do
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0084 0x00
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0085 0x0b
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0086 0x26 
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0087 0x01
        ${TOOL_100_PY} w phy ${CHN} $lane 0x0090 0x01
        ${TOOL_100_PY} r phy ${CHN} $lane 0x008a
        ${TOOL_100_PY} r phy ${CHN} $lane 0x008b
        ${TOOL_100_PY} w phy ${CHN} $lane 0x008a 0x80
    done
}

case $ACTION in
    "close")
        echo $ACTION
        if grep -q "open" dr_switch.sh; then
            patch dr_switch.sh < close.patch
        fi
        ;;
    "open")
        echo $ACTION
        if grep -q "close" dr_switch.sh; then
            patch dr_switch.sh -R < close.patch
        fi
        ;;
    *)
        echo "cmd error"
        exit 2
        ;;
esac

action_colse_open

case $MODE in 
    exter)
        mode_exter
        ;;
    loop)
        mode_loop
        ;;
esac

${TOOL_100_PY} w mac ${CHN} 0x310 0x0


