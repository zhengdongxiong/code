#!/bin/bash

echo "init for autoinstall"

mv /etc/rc.local /etc/rc.local.back

cat >/etc/rc.local <<EOF
#!/bin/bash


bash /cdrom/install/install.sh

EOF

chmod +x /etc/rc.local

exec /sbin/init
