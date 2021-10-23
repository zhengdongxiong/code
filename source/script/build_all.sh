#!/bin/bash

SCRIPT_DIR=${PWD}/../
BUILD_DIR=${PWD}/../../build/
INSTALL_DIR=${PWD}/../../install/
BINARY_DIR=${PWD}/../../binary/

cp ../../config/c3000_defconfig arch/x86/configs/c3000_defconfig || exit 1

make O=${BUILD_DIR} c3000_defconfig \
	&& make O=${BUILD_DIR} menuconfig \
	&& make O=${BUILD_DIR} bzImage modules -j16 \
	|| exit 1

test -d /boot        && mv /boot /boot-back
test -d /lib/modules && mv /lib/modules /lib/modules-back

mkdir -p /boot
mkdir -p /lib/modules

INSTALL_MOD_STRIP=1 make O=${BUILD_DIR} modules_install install
rm -rf   ${INSTALL_DIR}
mkdir -p ${INSTALL_DIR}/
mkdir -p ${INSTALL_DIR}/lib/

mv /boot        ${INSTALL_DIR}/boot
mv /lib/modules ${INSTALL_DIR}/lib/modules

test -d /boot-back        && mv /boot-back /boot
test -d /lib/modules-back && mv /lib/modules-back /lib/modules

rm -f ${INSTALL_DIR}/lib/modules/*/{build,source}

mkdir -p ${BINARY_DIR}
tar -zcf ${BINARY_DIR}/linux-4.4.167.bin.tar.gz -C ${INSTALL_DIR} . \
	|| exit 1

rm -rf   ${BINARY_DIR}/linux-headers-4.4.167
mkdir -p ${BINARY_DIR}/linux-headers-4.4.167

bash ${SCRIPT_DIR}/find-linux-headers.sh \
	>${BINARY_DIR}/linux-headers-4.4.167/src-list.txt \
	|| exit 1

tar -cf ${BINARY_DIR}/linux-headers-4.4.167/src-headers.tar \
	-C . -T ${BINARY_DIR}/linux-headers-4.4.167/src-list.txt \
	|| exit 1

cd ${BUILD_DIR} \
&& bash ${SCRIPT_DIR}/find-linux-headers.sh \
	>${BINARY_DIR}/linux-headers-4.4.167/out-list.txt \
	&& cd - || exit 1

tar -cf ${BINARY_DIR}/linux-headers-4.4.167/out-headers.tar \
	-C ${BUILD_DIR} -T ${BINARY_DIR}/linux-headers-4.4.167/out-list.txt \
	|| exit 1

cd ${BINARY_DIR}/linux-headers-4.4.167/ \
	&& tar -xf out-headers.tar \
	&& tar -xf src-headers.tar \
	&& rm -f out-headers.tar src-headers.tar out-list.txt src-list.txt \
	&& tar -zcf ../linux-headers-4.4.167.tar.gz . \
	&& cd -

