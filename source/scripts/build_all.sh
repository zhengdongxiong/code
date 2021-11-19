#!/bin/bash

export ARCH=arm64 
export PATH=$PATH:/opt/gcc-linaro-6.1.1-2016.08-x86_64_aarch64-linux-gnu/bin 
export CROSS_COMPILE=aarch64-linux-gnu-

SOURCE_DIR=${PWD}
SCRIPT_DIR=${PWD}/../
BUILD_DIR=${PWD}/../../build/
INSTALL_DIR=${PWD}/../../install/
BINARY_DIR=${PWD}/../../binary/

version="4.4.233"

cp ../../config/ft2000ahk_defconfig arch/arm64/configs/

make O=${BUILD_DIR} ft2000ahk_defconfig \
    && make O=${BUILD_DIR} menuconfig \
    && make O=${BUILD_DIR} all -j24 \
    || exit 1

rm -rf   ${INSTALL_DIR}
mkdir -p ${INSTALL_DIR}/boot

INSTALL_PATH=${INSTALL_DIR}/boot make O=${BUILD_DIR} install
INSTALL_MOD_STRIP=1 INSTALL_MOD_PATH=${INSTALL_DIR} make O=${BUILD_DIR} modules_install


#名字修改
cd ${INSTALL_DIR}/boot \
	&& mkimage -n 'linux-4.4.233' -A arm64 -O linux -C none \
	-a 0x80080000 -e 0x80080000 -d vmlinuz-${version} uImage-${version} \
	&& cd -

rm -f ${INSTALL_DIR}/lib/modules/*/{build,source}

mkdir -p ${BINARY_DIR}

tar -zcf ${BINARY_DIR}/linux-$version.bin.tar.gz -C ${INSTALL_DIR} . \
    || exit 1

rm -rf   ${INSTALL_DIR}/linux-headers-$version
mkdir -p ${INSTALL_DIR}/linux-headers-$version

bash ${SCRIPT_DIR}/find-linux-headers.sh \
    >${INSTALL_DIR}/linux-headers-$version/src-list.txt \
    || exit 1

tar -cf ${INSTALL_DIR}/linux-headers-$version/src-headers.tar \
    -C . -T ${INSTALL_DIR}/linux-headers-$version/src-list.txt \
    || exit 1

cd ${BUILD_DIR} \
&& bash ${SCRIPT_DIR}/find-linux-headers.sh \
    >${INSTALL_DIR}/linux-headers-$version/out-list.txt \
    && cd - || exit 1

tar -cf ${INSTALL_DIR}/linux-headers-$version/out-headers.tar \
    -C ${BUILD_DIR} -T ${INSTALL_DIR}/linux-headers-$version/out-list.txt \
    || exit 1

cd ${INSTALL_DIR}/linux-headers-$version/ \
    && tar -xf out-headers.tar \
    && tar -xf src-headers.tar \
    && rm  -f out-headers.tar src-headers.tar out-list.txt src-list.txt \
    && tar -zcf ${BINARY_DIR}/linux-headers-$version.tar.gz -C ../ linux-headers-$version

