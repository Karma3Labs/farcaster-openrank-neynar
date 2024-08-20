sudo useradd -M -s /usr/sbin/nologin openrank

sudo mkdir -p /home/openrank/.ssh
cat << EOF | sudo tee /home/openrank/.ssh/authorized_keys
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIC4J7BpIz1LKwP0F+/uQuoyiSGeDS1SpGcG07XJ4o2C openrank
EOF
sudo chmod 700 /home/openrank/.ssh
sudo chmod 600 /home/openrank/.ssh/authorized_keys
sudo chown -R openrank:openrank /home/openrank/.ssh

cat << EOF | sudo tee /etc/ssh/sshd_config.d/openrank.conf
Match User openrank
    AllowTcpForwarding yes
    X11Forwarding no
    PermitTunnel yes
    ForceCommand echo 'This account can only be used for tunneling'
EOF

# It may be called "sshd" in older versions of Ubuntu or other flavors of Linux
sudo systemctl restart ssh.service

