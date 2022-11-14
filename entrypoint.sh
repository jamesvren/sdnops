#!/bin/bash

vip=${INT_VIP:-"0.0.0.0"}
port=${WEB_PORT:-7787}
host=$(ip route list match ${vip} scope link | awk '{printf "%s", $7}')
export MYIP=${host}

# Start respondent in background
python3 /root/message.py respondent &

# Start web server, it should only be started in controller nodes
if [ "${NODE_MODE}" == "survey" ]; then
    uvicorn --host $host --port $port web:app
fi
