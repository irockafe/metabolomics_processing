#! /bin/bash
## Install Docker
## https://docs.docker.com/install/linux/docker-ce/debian/#set-up-the-repository
# For debian
sudo apt-get remove docker docker-engine docker.io
sudo apt-get update
wait
# Jessie or newer
sudo apt-get install \
     apt-transport-https \
     ca-certificates \
     curl \
     gnupg2 \
     software-properties-common
wait
# Add Docker's gpg key
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
# Check the fingerprint
sudo apt-key fingerprint 0EBFCD88
# Add repo so apt-get can use it
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable"
wait
# Had an issue here where apt-get update was running in background
# had to use ps -aux | grep apt to find the process, kill it and restart from here
sudo apt-get update
wait
sudo apt-get install docker-ce
wait
# Make the root directory for data storage in /home/
# (the same place where data volume is mounted)
# then restart it
sudo sh -c 'echo {\"data-root\": \"/home/docker\"} >> /etc/docker/daemon.json'
sudo systemctl stop docker && sudo systemctl start docker
# Check that it works
sudo docker run hello-world
# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.23.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
wait
sudo chmod +x /usr/local/bin/docker-compose
# Check that it works
sudo docker-compose --version

# Lastly, install git
sudo apt-get install git

# sudo autocomplete doesn't work. Might be because part of different groups. I dunno
