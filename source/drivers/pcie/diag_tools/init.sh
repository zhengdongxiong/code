#!/bin/bash

DRIVER_DIR=driver
USER_TOOL=fpgarw

make -C ${DRIVER_DIR} && insmod ${DRIVER_DIR}/*.ko
cp ${USER_TOOL} /usr/bin
