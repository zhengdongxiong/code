#!/bin/bash

echo "##########################################"
id_boot=1
id_isos=2
id_lvm=3

echo "##########################################"
if cat /proc/cmdline | grep "\<iso-scan\>" >/dev/null ; then
        src_disk=`cat /proc/mounts | grep "/isodevice\>" | cut -d' ' -f 1 | sed -e 's/[0-9]*$//'`
else
        src_disk=`cat /proc/mounts | grep "/cdrom\>" | cut -d' ' -f 1 | sed -e 's/[0-9]*$//'`
fi
echo "source disk is '${src_disk}'"

dst_disk=`fdisk -l | grep "\<Disk\> /" | grep -v "${src_disk}" | grep -v "/dev/ram" | grep -v "/dev/loop" | grep -v "/dev/mapper/" | head -n 1`

if [ -z "${dst_disk}" ]; then
    echo "no avaliable disk found to install OS!"
    echo "abort!"
    exit 1;
fi

echo "dest disk is '${dst_disk}'"

dst_disk=`echo ${dst_disk} | cut -d':' -f 1 | cut -d' ' -f 2`

echo "##########################################"

swapoff -a 

swap_present=`cat /proc/swaps | tail -n +2`
if [ "x${swap_present}" != "x" ]; then
	swap_blk=`blkid | grep swap | awk -F: '{print $1}'`
	swapoff ${swap_blk}
fi

vgchange -an

oldvg=`vgdisplay  | grep "VG Name" | sed -e 's/VG Name//' | sed -e 's/ //g'`
if [ "x${oldvg}" != "x" ]; then
    echo "remove old vg '${oldvg}'"
    vgremove -f "${oldvg}"
fi

echo "##########################################"
#dd if=/dev/zero of=${dst_disk} bs=1k count=1k
#sgdisk -p ${dst_disk}
parted -s ${dst_disk} mklabel msdos && \
        partprobe ${dst_disk} ||
        (echo "############## ERROR ##############"; exit 1)


echo "##########################################"
echo "create partition"
#parted -s /dev/sda mkpart primary 0 1G
#parted -s /dev/sda mkpart primary 1G 21G
#parted -s /dev/sda mkpart extended 21G 100%
#parted -s /dev/sda mkpart logic linux-swap 21G 100%

#kernel dtb initrd.img
parted -s  ${dst_disk} mkpart primary 0% 2G
#os
parted -s  ${dst_disk} mkpart primary 2G 7G
#lvm
parted -s  ${dst_disk} mkpart primary 7G 100%

echo "##########################################"
echo "create PV"
pvcreate ${dst_disk}${id_lvm}

echo "##########################################"
echo "create VG"
vgcreate ubuntu-vg ${dst_disk}${id_lvm}

echo "##########################################"
echo "create LV for sysfs"
yes | lvcreate -n sysfs -L 500M ubuntu-vg

echo "##########################################"
echo "create LV for appfs"
yes | lvcreate -n appfs -L 4G ubuntu-vg

echo "##########################################"
echo "create LV for configfs"
yes | lvcreate -n configfs -L 100M ubuntu-vg

echo "##########################################"
echo "create LV for logfs"
yes | lvcreate -n logfs -L 2G ubuntu-vg

echo "##########################################"
echo "create LV for swap"
yes | lvcreate -n swap -L 4G ubuntu-vg

echo "##########################################"
echo "create LV for apprun"
yes | lvcreate -n apprun -l 100%FREE ubuntu-vg

echo "##########################################"
echo "format partition for boot"
yes | mkfs.ext4 ${dst_disk}${id_boot}

echo "##########################################"
echo "format partition for isos"
yes | mkfs.ext4 ${dst_disk}${id_isos}

echo "##########################################"
echo "format LV for sysfs"
yes | mkfs.ext4 /dev/ubuntu-vg/sysfs

echo "##########################################"
echo "format LV for appfs"
yes | mkfs.ext4 /dev/ubuntu-vg/appfs

echo "##########################################"
echo "format LV for configfs"
yes | mkfs.ext4 /dev/ubuntu-vg/configfs

echo "##########################################"
echo "format LV for logfs"
yes | mkfs.ext4 /dev/ubuntu-vg/logfs

echo "##########################################"
echo "format LV for apprun"
yes | mkfs.ext4 /dev/ubuntu-vg/apprun

echo "##########################################"
uuid_part_boot=`blkid ${dst_disk}${id_boot} | sed -ne 's/.*\<UUID\>="\([^"]\+\)".*/\1/p'`
echo "UUID of BOOT partition '${uuid_part_boot}'"
echo "##########################################"
uuid_part_isos=`blkid ${dst_disk}${id_isos} | sed -ne 's/.*\<UUID\>="\([^"]\+\)".*/\1/p'`
echo "UUID of isos partition '${uuid_part_isos}'"

mkdir -p /target/boot && \
        mount --uuid "${uuid_part_boot}" /target/boot && \
        mkdir -p /target/isodevice && \
        mount --uuid "${uuid_part_isos}" /target/isodevice || \
		fail=y
		
if [ "x${fail}" = "xy" ]; then
        echo "############## ERROR ##############"
        exit 1
fi


echo "##########################################"
echo "install filesystem"

rsync -q -av --one-file-system /rofs/boot/ /target/boot

version=`cat /cdrom/version | head -n 1`
iso_name="OS-phytium-uboot-20.04-${version}.iso"

mkdir -p /target/isodevice/isos/root
rsync -ap --exclude=lost+found  \
	--exclude="System Volume Information" \
	/cdrom/ /target/isodevice/isos/root

mkisofs -r \
	-J -joliet-long \
	-o /target/isodevice/isos/${iso_name} \
	/target/isodevice/isos/root/

ln -sf ${iso_name} /target/isodevice/isos/default

rm -rf /target/isodevice/isos/root/

umount /target/boot
umount /target/isodevice

echo "Finish!"



