#! /usr/bin/env bash 
set -e 

NET_ADMIN_HOME="${HOME}/net-admin"
echo "NET_ADMIN_HOME: ${NET_ADMIN_HOME}" 

echo "Start Network Admin service..." 
cd "${NET_ADMIN_HOME}" 
python ./web-service/net-admin.py -c ./web-service/net-admin.json 
echo "Network Admin service stopped" 
