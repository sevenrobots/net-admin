#! /usr/bin/env bash 
set -e 

# depedent software and tools   
sudo apt-get update \
    && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3-websockets \
        python3-netifaces \
    && sudo apt-get autoremove \
    && sudo apt-get clean \
    && sudo rm -rf /var/lib/apt/lists/*

# important locations   
SYSTEM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" 
NET_ADMIN_HOME="$(cd "${SYSTEM_DIR}/.." && pwd)" 
echo "SYSTEM_DIR: ${SYSTEM_DIR}" 
echo "NET_ADMIN_HOME: ${NET_ADMIN_HOME}" 

# install entry script for net-admin  
echo "Install net-admin start script..." 
cat "${SYSTEM_DIR}/net-admin.sh" 
echo "" 
sed -i "s/^\([[:space:]]*NET_ADMIN_HOME[[:space:]]*=\)[[:space:]]*.*/\1\"${NET_ADMIN_HOME//\//\\/}\"/" "${SYSTEM_DIR}/net-admin.sh"
cat "${SYSTEM_DIR}/net-admin.sh" 
echo "" 
sudo cp -r ${SYSTEM_DIR}/net-admin.sh /usr/local/bin/net-admin.sh 
sudo chmod a+x /usr/local/bin/net-admin.sh 

# install systemd service for net-admin 
echo "Install net-admin service..." 
sudo cp -f "${SYSTEM_DIR}/net-admin.service" /etc/systemd/system/net-admin.service 
sudo chmod 644 /etc/systemd/system/net-admin.service  
sudo systemctl enable net-admin 
echo "net-admin service enabled" 
