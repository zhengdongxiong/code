#!/bin/bash

echo "##########################################"
id_boot=1
id_lvm=2
#id_swap=3
#id_efi=3

VERSION="4.4.233"

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

#/boot
parted -s  ${dst_disk} mkpart primary 0% 5G
#lvm
parted -s  ${dst_disk} mkpart primary 5G 100%

echo "##########################################"
echo "create PV"
pvcreate ${dst_disk}${id_lvm}

echo "##########################################"
echo "create VG"
vgcreate ubuntu-ft ${dst_disk}${id_lvm}

echo "##########################################"
echo "create LV for swap"
yes | lvcreate -n swap -L 4G ubuntu-ft

echo "##########################################"
echo "create LV for root"
yes | lvcreate -n root -l 100%FREE ubuntu-ft

echo "##########################################"
echo "format partition for boot"
yes | mkfs.ext4 ${dst_disk}${id_boot}

echo "##########################################"
echo "format partition for root"
yes | mkfs.ext4 /dev/ubuntu-ft/root

echo "##########################################"
echo "format partition for swap"
yes | mkswap /dev/ubuntu-ft/swap

echo "##########################################"
uuid_part_boot=`blkid ${dst_disk}${id_boot} | sed -ne 's/.*\<UUID\>="\([^"]\+\)".*/\1/p'`
echo "UUID of BOOT partition '${uuid_part_boot}'"

mkdir -p /target/ && \
        mount /dev/ubuntu-ft/root /target && \
        mkdir -p /target/boot && \
        mount --uuid "${uuid_part_boot}" /target/boot || \
		fail=y
		
if [ "x${fail}" = "xy" ]; then
        echo "############## ERROR ##############"
        exit 1
fi

echo "##########################################"
cat >/tmp/printdot.sh <<EOF
while [ ! -f /tmp/.done ]; do echo -n "."; sleep 1; done
rm -rf /tmp/.done
echo
echo
echo
echo "Finish!"
echo "You can reboot to enjoy the new system! (make sure to boot from your hard disk)"
echo
echo
echo
EOF
chmod +x /tmp/printdot.sh

echo "##########################################"
echo "install filesystem"

#echo "##########################################"
#mount -o ro /cdrom/casper/filesystem.squashfs  /mnt

#bash /tmp/printdot.sh &

rsync -q -av --one-file-system /rofs/ /target
#umount /mnt

echo "127.0.0.1 localhost" > /target/etc/hosts
#update-initramfs may use swap 
#echo "RESUME=UUID=${uuid_part_swap}" > /target/etc/initramfs-tools/conf.d/resume

cat >/target/etc/fstab <<EOF
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
UUID=${uuid_part_boot}  /boot     ext4 defaults          0 2
/dev/ubuntu-ft/root     /         ext4 errors=remount-ro 0 1
/dev/ubuntu-ft/swap   none      swap sw                0 0
EOF

mkdir -p /target/{dev,proc,sys,run}
mount  --bind  /dev/ /target/dev
mount -t proc  proc  /target/proc
mount -t sysfs sysfs /target/sys
mount -o bind  /run  /target/run

chroot /target/ /bin/bash -c "touch /etc/shadow;pwconv"

chroot /target/ /bin/bash -c "echo 'root:\$1\$.deOvMaW\$hWn4Fvw5WEUryKmw3Zm1n1' | chpasswd -e"

chroot /target/ /bin/bash -c "mount -a;swapon -a"

umount /target/run
umount /target/sys
umount /target/proc
umount -l /target/dev
umount /target/boot
umount /target

echo "Finish!"

#touch /tmp/.done

