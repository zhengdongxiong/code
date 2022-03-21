#!/bin/bash

SW8180_DIRVER=cpld/sw8180-cpld.c

VERSION=v1.2

line=`grep -n ^MODULE_VERSION ${SW8180_DIRVER} | awk -F: '{print $1}'`
sed -i "${line}cMODULE_VERSION(\"${VERSION}\");" ${SW8180_DIRVER}

tar -zcf cpld-${VERSION}.tar.gz --exclude=cpld/81-sw8180.rules cpld/ 


