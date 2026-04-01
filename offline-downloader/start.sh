#!/bin/bash

# 启动aria2
aria2c --daemon --enable-rpc --rpc-listen-all --rpc-allow-origin-all --dir=/download

# 启动Flask应用
cd /app && python3 app.py &

# 启动Nginx
nginx -g "daemon off;"
