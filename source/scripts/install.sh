#!/bin/bash

echo "##########################################"
<<EOF
id_bios_grub=1
id_efi=2
id_boot=3
id_lvm=4

echo "##########################################"
if cat /proc/cmdline | grep "\<iso-scan\>" >/dev/null ; then
    src_disk=`cat /proc/mounts | grep "/isodevice\>" | cut -d' ' -f 1 | sed -e 's/[0-9]*$//'`
else
    src_disk=`cat /proc/mounts | grep "/cdrom\>" | cut -d' ' -f 1 | sed -e 's/[0-9]*$//'`
fi

EOF

id_efi=1
id_boot=2
id_lvm=3

echo "##########################################"
src_disk=`cat /proc/mounts | grep "/cdrom\>" | cut -d' ' -f 1 | sed -e 's/[0-9]*$//'`

echo "source disk is '${src_disk}'"

dst_disk=`sfdisk -l | grep "\<Disk\> /" | grep -v "${src_disk}" | grep -v "/dev/loop" | grep -v "/dev/mapper/" | head -n 1`

if [ -z "${dst_disk}" ]; then
    echo "no avaliable disk found to install OS!"
    echo "abort!"
    exit 1;
fi

echo "dest disk is '${dst_disk}'"

dst_disk=`echo ${dst_disk} | cut -d':' -f 1 | cut -d' ' -f 2`

echo "##########################################"
swapoff -a

vgchange -an

oldvg=`vgdisplay  | grep "VG Name" | sed -e 's/VG Name//' | sed -e 's/ //g'`
if [ "x${oldvg}" != "x" ]; then
    echo "remove old vg '${oldvg}'"
    vgremove -f "${oldvg}"
fi

echo "##########################################"
#dd if=/dev/zero of=${dst_disk} bs=1k count=1k
#sgdisk -p ${dst_disk}
sgdisk -g -o ${dst_disk} && \
        sgdisk -Z ${dst_disk} && \
        partprobe ${dst_disk} ||
        (echo "############## ERROR ##############"; exit 1)
#partx -d ${dst_disk}


<<EOF
echo "##########################################"
echo "create partition for legacy bios"
sgdisk -n ${id_bios_grub}:0:+2M ${dst_disk}
parted ${dst_disk} set 1 bios_grub on
EOF

echo "##########################################"
echo "create partition for efi"
sgdisk -n ${id_efi}:0:+128M ${dst_disk}
sgdisk -t ${id_efi}:0xef00 ${dst_disk} #EFI System

echo "##########################################"
echo "create partition for boot"
sgdisk -n ${id_boot}:0:+1G ${dst_disk}

echo "##########################################"
echo "create LVM"
sgdisk -n ${id_lvm}:0:0 ${dst_disk}
sgdisk -t ${id_lvm}:0x8e00 ${dst_disk} #Linux LVM

echo "##########################################"
echo "create PV"
pvcreate ${dst_disk}${id_lvm}

echo "##########################################"
echo "create VG"
vgcreate ubuntu-vg ${dst_disk}${id_lvm}

echo "##########################################"
echo "create LV for swap"
yes | lvcreate -n swap -L 4G ubuntu-vg

echo "##########################################"
echo "create LV for root"
yes | lvcreate -n root -l 100%FREE ubuntu-vg

echo "##########################################"
echo "format partition for efi"
yes | mkfs.vfat ${dst_disk}${id_efi}

echo "##########################################"
echo "format artition for boot"
yes | mkfs.ext2 ${dst_disk}${id_boot}

echo "##########################################"
echo "format LV for root"
yes | mkfs.ext4 /dev/ubuntu-vg/root

echo "##########################################"
echo "format LV for swap"
yes | mkswap    /dev/ubuntu-vg/swap

echo "##########################################"
uuid_part_efi=`blkid ${dst_disk}${id_efi} | sed -ne 's/.*\<UUID\>="\([^"]\+\)".*/\1/p'`
echo "UUID of EFI partition '${uuid_part_efi}'"
uuid_part_boot=`blkid ${dst_disk}${id_boot} | sed -ne 's/.*\<UUID\>="\([^"]\+\)".*/\1/p'`
echo "UUID of BOOT partition '${uuid_part_boot}'"
echo "##########################################"

mkdir -p /target/ && \
        mount /dev/ubuntu-vg/root /target && \
        mkdir -p /target/boot && \
        mount --uuid "${uuid_part_boot}" /target/boot && \
        mkdir -p /target/boot/efi && \
        mount --uuid "${uuid_part_efi}" /target/boot/efi || \
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

echo "##########################################"
mount -o ro /cdrom/casper/filesystem.squashfs  /mnt
echo "##########################################"


rsync -q -av --one-file-system /mnt/ /target

echo "127.0.0.1 localhost" >/target/etc/hosts
#update-initramfs may use swap 
echo "RESUME=/dev/ubuntu-vg/swap" > /target/etc/initramfs-tools/conf.d/resume

cat >/target/etc/fstab <<EOF
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
UUID=${uuid_part_efi}   /boot/efi vfat defaults,nodev          0 1
UUID=${uuid_part_boot}  /boot     ext2 defaults,nodev          0 2
/dev/ubuntu-vg/root     /         ext4 errors=remount-ro 0 1
/dev/ubuntu-vg/swap   none      swap sw                0 0

EOF

mkdir -p /target/{dev,proc,sys,run}
mount  --bind  /dev/ /target/dev
mount -t proc  proc  /target/proc
mount -t sysfs sysfs /target/sys
mount -o bind  /run  /target/run

cp -r /cdrom/configs/* /target/

chroot /target/ /bin/bash -c "touch /etc/shadow;pwconv"
chroot /target/ /bin/bash -c "echo 'root:\$1\$.deOvMaW\$hWn4Fvw5WEUryKmw3Zm1n1' | chpasswd -e"

#--target=i386-pc x86_64-efi see man grub-install
#chroot /target/ /bin/bash -c "grub-install --no-floppy --force --target=i386-pc ${dst_disk}"
#BOOTX64.CSV shimx64.efi,ubuntu,,This is the boot entry for ubuntu
chroot /target/ /bin/bash -c "grub-install --no-floppy --force --target=x86_64-efi --uefi-secure-boot ${dst_disk}"
chroot /target/ /bin/bash -c "mount -a;swapon -a"
chroot /target/ /bin/bash -c "update-grub"

umount /mnt
umount /target/dev
umount /target/proc
umount /target/sys
umount /target/run

umount /target/boot/efi
umount /target/boot
umount /target



