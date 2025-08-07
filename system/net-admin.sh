#! /usr/bin/env bash 
set -e 

ADMIN_HOME="${HOME}/net-admin/web-ui"
echo "ADMIN_HOME: ${ADMIN_HOME}" 

echo "Start Network Admin service..." 
cd "${ADMIN_HOME}" 
python net-admin.py -c net-admin.json 
echo "Network Admin service stopped" 
