#!/bin/bash
# Add any other apt repos here
sudo apt update

# Install
sudo apt-get install mysql-client gcc -y --no-install-recommends
sudo apt-get clean
rm -rf /var/lib/apt/lists/*

# Other installation
wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq
chmod +x /usr/bin/yq