#!/bin/bash

VERSION=V0.18

MAKE_PWD=${PWD}

test -d /opt/gcc-linaro-6.1.1-2016.08-x86_64_aarch64-linux-gnu || { echo "not found aarch64-gcc_tool"; exit 1; }
AARCH_PATH="/opt/gcc-linaro-6.1.1-2016.08-x86_64_aarch64-linux-gnu/bin"
export PATH=$PATH:${AARCH_PATH}
export CC=aarch64-linux-gnu-gcc
export ARCH=arm
export CROSS_COMPILE=aarch64-linux-gnu-
export CXX=aarch64-linux-gnu-g++
host="--host=arm"


TOOLS_DIR=tools
BUILD_DIR=build

i2c_tool="i2c/i2c-tools-4.1"
memtester_tool="memtester/memtester-4.3.0"
ncures_lib="ncurses/ncurses-6.2"
minicom_tool="minicom/minicom-2.7.1"
ethtool_tool="ethtool/ethtool-4.19"
can_lib="can/libsocketcan-0.0.11"
can_tool="can/canutils-4.0.6"
iperf_tool="iperf/iperf-2.0.9"
fru_rw_tool="fru/fru_rw"
fru_sim_tool="fru/fru_sim"
tcpdump_lib="tcpdump/libpcap-1.9.1"
tcpdump_tool="tcpdump/tcpdump-4.9.3"
fio_tool="fio/fio-2.1.10"
ltp_tool="ltp/ltp"
iozone_tool="iozone/iozone3_397"

ALL_SUB_DIR="devmem mdio ${i2c_tool} ${memtester_tool} ${ncures_lib}
            ${minicom_tool} ${ethtool_tool} ${can_lib} ${can_tool}
            ${iperf_tool} ${fru_rw_tool} ${fru_sim_tool} ${iozone_tool}
            ${tcpdump_lib} ${tcpdump_tool} ${ltp_tool} ${fio_tool}"
            
#ALL_SUB_DIR="${fru_rw_tool}"


function show_usage()
{
    cat << EOF
Usage:
  $1 <opt>
      opt: diag "Only diag tools"
           ltp  "Only ltp tools "
           all  "Compile tools and package"
Example:
  $1 diag
  $1 all  
EOF
}


function build_all()
{
    for src_dir in $@; do
        test -d $src_dir || { echo "not found $src_dir "; exit 1;} 
        case $src_dir in 
            ${ethtool_tool}|${iperf_tool}|${can_lib}|${tcpdump_lib}|${tcpdump_tool}) 
                test -d $src_dir/out || mkdir -p $src_dir/out
                cd $src_dir
                autoreconf -ivf
                ./configure ${host} --prefix=${MAKE_PWD}/$src_dir/out || { echo "config $src_dir fail "; exit 1;}
                make -j24 || { echo "make $src_dir fail "; exit 1;}
                make install
                cd - >> /dev/null
                ;; 
            ${can_tool}) 
                test -d $src_dir/out || mkdir -p $src_dir/out
                test -d ${can_lib}/out/include || { echo "not found lib"; \
                    exit 1; }
                cp ${can_lib}/out/include/* $src_dir/include 
                cd $src_dir
                autoreconf -ivf
                ./configure ${host} --prefix=${MAKE_PWD}/$src_dir/out \
                    libsocketcan_LIBS=-lsocketcan \
                    LDFLAGS=-L${MAKE_PWD}/${can_lib}/out/lib \
                    libsocketcan_CFLAGS=-I${MAKE_PWD}/${can_lib}/out/include || \
                    { echo "config $src_dir fail "; exit 1;}
                make -j24 || { echo "make $src_dir fail "; exit 1;}
                make install
                cd - >> /dev/null

                ;;
            ${ncures_lib})
                test -d $src_dir/out || mkdir -p $src_dir/out
                cd $src_dir
                ./configure ${host} --prefix=${MAKE_PWD}/$src_dir/out || { echo "config $src_dir fail "; exit 1;}
                make -j24 || { echo "make $src_dir fail "; exit 1;}
                make install
                cd - >> /dev/null

                ;; 
            ${minicom_tool})
                test -d $src_dir/out || mkdir -p $src_dir/out
                cd $src_dir
                autoreconf -ivf
                ./configure ${host} --prefix=${MAKE_PWD}/$src_dir/out \
                    LDFLAGS=-L${MAKE_PWD}/${ncures_lib}/out/lib \
                    CFLAGS=-I${MAKE_PWD}/${ncures_lib}/include || \
                    { echo "config $src_dir fail "; exit 1;}
                make -j24 || { echo "make $src_dir fail "; exit 1;}
                make install 
                cd - >> /dev/null
                ;;
            ${fru_rw_tool}|${fru_sim_tool}) 
                make -C $src_dir all -j24 || { echo "make $src_dir fail "; exit 1;}
                ;;
            ${ltp_tool})
                cd $src_dir
                make autotools
                ./configure --prefix=${MAKE_PWD}/$src_dir/ltp-tools ${host} || \
                    { echo "config $src_dir fail "; exit 1;}
                make -j24
                make -j24 || { echo "make $src_dir fail "; exit 1;}
                make install
                cd - >> /dev/null
                ;;
            ${iozone_tool}) 
                make -C $src_dir/src/current/ linux-arm -j24 || { echo "make $src_dir fail "; exit 1;}
                ;;
            *) 
                make -C $src_dir -j24 || { echo "make $src_dir fail "; exit 1;}
                ;;
        esac 
    done
    
}

function build_cp()
{
    for src_dir in $@
    do
        case $src_dir in 
            ${can_tool}) 
                cp -r $src_dir/out/bin/*  $BUILD_DIR/
                cp -r $src_dir/out/sbin/*  $BUILD_DIR/
                ;; 
            ${iperf_tool}) 
                cp -r $src_dir/out/bin/*  $BUILD_DIR/
                ;;
            ${i2c_tool}) 
                cd $src_dir/tools 
                cp ../lib/libi2c.so.0.1.1 i2cdetect i2cdump i2cget i2cset i2ctransfer -t ${MAKE_PWD}/$BUILD_DIR/
                cd - >> /dev/null 
                ;;
            ${memtester_tool}) 
                cp $src_dir/memtester $BUILD_DIR/ 
                ;; 
            ${ethtool_tool}) 
                cp $src_dir/out/sbin/* $BUILD_DIR/ 
                ;; 
            ${tcpdump_tool}) 
                cp $src_dir/out/sbin/tcpdump $BUILD_DIR/ 
                ;; 
            ${minicom_tool}) 
                cp -r $src_dir/out/bin/minicom  $BUILD_DIR/
                ;; 
            ${fru_rw_tool}|${fru_sim_tool}) 
                cp -r $src_dir/apps_dir/*  $BUILD_DIR/
                ;;
            ${fio_tool}) 
                cp -r $src_dir/fio  $BUILD_DIR/
                ;; 
            #ltp too large, use in ltp/ltp-tools
            ${ltp_tool})
                cp -r $src_dir/ltp-tools ltp/
                ;;
            ${iozone_tool}) 
                cp $src_dir/src/current/iozone $BUILD_DIR/
                ;;
        esac
    done
}

function pack_ltp()
{
    tar -zcf ltp.tar.gz -C ltp/ ltp-tools
    chmod +x *.tar.gz
    mv *.tar.gz ../version
}

function pack_diag()
{
    cp -r $BUILD_DIR/* $TOOLS_DIR
    tar -zcf diag_tools_${VERSION}.tar.gz $TOOLS_DIR 
    chmod +x *.tar.gz
    mv *.tar.gz ../version
    find $TOOLS_DIR/ -maxdepth 1 \
                     \( ! -name "*.sh" -a  \
                        ! -name "*.py" -a  \
                        ! -name "tools" \) \
                        -exec rm -rf {} \;
    
}



case $1 in 
    diag)
        pack_diag
        ;;
    ltp)
        pack_ltp
        ;;
    all)
        build_all ${ALL_SUB_DIR}
        build_cp ${ALL_SUB_DIR}
        pack_diag
        pack_ltp
        ;;
    *)
        show_usage $0
        ;;
esac
