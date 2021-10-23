#!/bin/bash

##################################################################

export LIVECD=/home/livecd
export WORK=${LIVECD}/work
export CD=${LIVECD}/cd
export FORMAT=squashfs
export FS_DIR=casper

mkdir -p ${CD}/${FS_DIR} ${WORK}/rootfs

#apt-get update

#apt-get install -y xorriso squashfs-tools tree minicom i2c-tools casper lupin-casper \
# gparted gdisk mtools grub-efi-amd64-bin grub-efi-ia32-bin grub-pc-bin 
 
#Copy your installation into the new filesystem

sudo rsync -q -av --one-file-system --exclude=/proc/* --exclude=/dev/* \
 --exclude=/sys/* --exclude=/tmp/* --exclude=/home/* --exclude=/lost+found \
 --exclude=/var/tmp/* --exclude=/boot/grub/* --exclude=/root/* \
 --exclude=/var/mail/* --exclude=/media/* \
 --exclude=/etc/fstab --exclude=/etc/mtab \
 --exclude=/etc/X11/xorg.conf* --exclude=/etc/gdm/custom.conf \
 --exclude=/etc/lightdm/lightdm.conf \
 --exclude=${LIVECD} --exclude=${LIVECD}/* \
 --exclude=/etc/oem/efi/* \
 #不要spool里面所有文件 要spool里面cron文件夹 要cron文件夹中所有
 --include=/var/spool/cron/ --include=/var/spool/cron/a* --exclude=/var/spool/* --exclude=/var/spool/cron/* \
 / ${WORK}/rootfs

cp -af /boot/* ${WORK}/rootfs/boot/

mount  --bind /dev/ ${WORK}/rootfs/dev
mount -t proc proc ${WORK}/rootfs/proc
mount -t sysfs sysfs ${WORK}/rootfs/sys
mount -o bind /run ${WORK}/rootfs/run

export kversion=`cd ${WORK}/rootfs/boot && ls -1 vmlinuz-* | tail -1 | sed 's@vmlinuz-@@'`

cat >${WORK}/rootfs/tmp.sh <<EOF
depmod -a \$(uname -r)
#update-initramfs -u -k \$(uname -r)
apt-get autoremove -y
apt-get clean

find /var/log -regex '.*?[0-9].*?' -exec rm -v {} \;

for i in \`cat /etc/passwd | awk -F":" '{print \$1}'\`
do
    uid=\`cat /etc/passwd | grep "^\${i}:" | awk -F":" '{print \$3}'\`
    [ "\$uid" -gt "998" -a "\$uid" -ne "65534" ] && userdel --force \${i} 2> /dev/null
done

find /var/log -type f | while read file
do
    cat /dev/null | tee $file
done

rm -f /etc/resolv.conf /etc/hostname

rm -rf /etc/lvm/archive /etc/lvm/backup

EOF

#cat ${WORK}/rootfs/tmp.sh

chroot ${WORK}/rootfs /bin/bash -c "bash /tmp.sh"

rm ${WORK}/rootfs/tmp.sh

cp -vp ${WORK}/rootfs/boot/vmlinuz-${kversion} ${CD}/${FS_DIR}/vmlinuz
cp -vp ${WORK}/rootfs/boot/initrd.img-${kversion} ${CD}/${FS_DIR}/initrd.img

chroot ${WORK}/rootfs dpkg-query -W --showformat='${Package} ${Version}\n' | sudo tee ${CD}/${FS_DIR}/filesystem.manifest

#Unmount bind mounted dirs:

umount ${WORK}/rootfs/run
umount ${WORK}/rootfs/sys
umount ${WORK}/rootfs/proc
umount ${WORK}/rootfs/dev

mksquashfs ${WORK}/rootfs ${CD}/${FS_DIR}/filesystem.${FORMAT} -noappend

echo -n $(du -s --block-size=1 ${WORK}/rootfs | tail -1 | awk '{print $1}') | tee ${CD}/${FS_DIR}/filesystem.size

find ${CD}/${FS_DIR}/ -type f -print0 | xargs -0 md5sum | sed "s@${CD}@.@" | grep -v md5sum.txt | tee -a ${CD}/md5sum.txt

