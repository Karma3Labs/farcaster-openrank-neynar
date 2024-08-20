DATA_DIR=/data
sudo fallocate -l 32G ${DATA_DIR}/swapfile
sudo chmod 600 ${DATA_DIR}/swapfile
sudo mkswap ${DATA_DIR}/swapfile
sudo swapon ${DATA_DIR}/swapfile
sudo sh -c 'echo "${DATA_DIR}/swapfile none swap sw 0 0" >> /etc/fstab'
sudo systemctl daemon-reload