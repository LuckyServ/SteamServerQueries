#!/bin/bash
#
# Script to get empty servers with part of arg1 in the info.
#
# Example: ./e chi
# 
# Author: Luckylock

python3 steamGameServer_A2S_INFO.py e < iplist | grep -i -e "$1" -e "Total" -B 1 -A 2
