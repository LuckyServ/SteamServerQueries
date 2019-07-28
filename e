#!/bin/bash
#
# Script to get empty servers with arg1 in the name.
#
# Example: ./e chi
# 
# Author: Luckylock

python3 steamGameServer_A2S_INFO.py e < iplist 2> failedConnections | grep -i -e "Name.*$1" -e "Total Players" -B 0 -A 4
