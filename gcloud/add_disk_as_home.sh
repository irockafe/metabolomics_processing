# Assumes a new disk is at /dev/sdb
DEVICE_ID="/dev/sdb"
MOUNT="/mnt/disk/disk"

# Format the disk
sudo mkfs.ext4 -m 0 -F -E lazy_itable_init=0,lazy_journal_init=0,discard $DEVICE_ID

sudo mkdir -p $MOUNT
sudo mount -o discard,defaults $DEVICE_ID $MOUNT
sudo chmod a+w $MOUNT
# Copy contents of /home to mounted disk
sudo mkdir /tmp/home
sudo cp -aR /home/* $MOUNT
sudo cp -aR /home/* /tmp/home
sudo rm -rf /home/*
sudo umount $MOUNT
sudo mount -o discard,defaults $DEVICE_ID /home
df -h

# Add disk to /etc/fstab
sudo cp /etc/fstab /etc/fstab.bak
DISK=$(sudo blkid -s UUID -o value /dev/sdb)
echo "UUID=$DISK /home ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
# Check what's in there
cat /etc/fstab
