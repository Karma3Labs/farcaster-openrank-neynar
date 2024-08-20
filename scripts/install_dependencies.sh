
# Install basic developer and build modules
sudo apt update
sudo apt install -y build-essential software-properties-common fail2ban

# Install Docker
sudo apt-get update
sudo apt-get upgrade
curl -fsSL test.docker.com -o get-docker.sh && sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Start the docker service
sudo systemctl enable docker.service
sudo systemctl start docker.service

# Install docker-compose
# List of releases are available at https://github.com/docker/compose/releases/tag/v2.27.0
ARCH=$(uname -m)
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-${ARCH} -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
sudo ln -sfn ~/.docker/cli-plugins/docker-compose /usr/bin/docker-compose


# # Create a security update script
# mkdir scripts
# cat > scripts/security-updates.sh  << EOF
# # Update the server
# export DEBIAN_FRONTEND=noninteractive
# export DEBIAN_PRIORITY=critical
# sudo -E apt-get -qy update
# sudo -E apt-get -qy install unattended-upgrades
# sudo -E apt-get -qy -o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confold" dist-upgrade
# sudo -E apt-get -qy autoclean
# EOF
# chmod 755 scripts/security-updates.sh
# ./scripts/security-updates.sh

# sudo reboot


