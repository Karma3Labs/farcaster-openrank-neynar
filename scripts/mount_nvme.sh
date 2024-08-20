yes | sudo mkfs.ext4 /dev/nvme1n1
sudo mkdir -p /mnt/nvme1n1
sudo mount /dev/nvme1n1 /mnt/nvme1n1
sudo blkid /dev/nvme1n1

# sudo reboot

UUID=$(sudo blkid -s UUID -o value /dev/nvme1n1)
FSTAB_ENTRY="UUID=$UUID /mnt/nvme1n1 ext4 defaults 0 2"
echo "$FSTAB_ENTRY" | sudo tee -a /etc/fstab

sudo mkdir /data
sudo chown -R ubuntu:ubuntu /data
sudo rsync -aXS /data /mnt/nvme1n1/
sudo umount /mnt/nvme1n1
sudo mount /dev/nvme1n1 /data

OLD_MOUNT_POINT="/mnt/nvme1n1"
NEW_MOUNT_POINT="/data"

# Backup the current fstab file
sudo cp /etc/fstab /etc/fstab.bak

# Replace the old mount point with the new mount point
sudo sed -i "s|$OLD_MOUNT_POINT|$NEW_MOUNT_POINT|g" /etc/fstab

sudo mount -a

