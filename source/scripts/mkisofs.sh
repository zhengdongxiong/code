#!/bin/sh

################################################################################
MAIN_INFO="UbuntuServer_16.04_X64"
IDENTIFIER=""
VERSION="V3.8.11"

FILENAME="OS_${MAIN_INFO}${IDENTIFIER}_${VERSION}.iso"

outputfile=./${FILENAME}

################################################################################
rm -rf root/{boot,efi,isolinux,oem}

/bin/cp -rf ./embedway_iso/{boot,efi,isolinux,oem} root/

sed -i -e "s/VERSION_ID/${VERSION}/g" root/boot/grub/grub.cfg
sed -i -e "s/VERSION_ID/${VERSION}/g" root/isolinux/txt.cfg

mkdir -p root/oem
echo "${VERSION}" > root/oem/iso_version

rm -rf root/ewx
ln -sf casper root/ewx

xorriso -as mkisofs \
 -J
 -isohybrid-mbr ./embedway_iso/my_isohdpfx.bin \
 -c isolinux/boot.cat \
 -b isolinux/isolinux.bin \
 -no-emul-boot \
 -boot-load-size 4 \
 -boot-info-table \
 -eltorito-alt-boot \
 -b boot/grub/efi.img \
 -no-emul-boot \
 -isohybrid-gpt-basdat \
 -o ${outputfile} \
 root/
