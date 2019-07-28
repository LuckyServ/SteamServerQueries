#!/bin/bash
#
# Script to get empty servers with arg1 in the name.
#
# Example: ./e chi
# 
# Author: Luckylock

python3 steamGameServer_A2S_INFO.py e < iplist | grep -i -e "Name.*$1" -B 1 -A 2
