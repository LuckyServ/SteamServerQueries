#!/bin/bash
#
# Script to get empty servers with part of arg1 in the name.
#
# Example: ./giveEmpty chi
# 
# Author: Luckylock

./steamGameServer_A2S_INFO.py < iplist e | grep -i -e "$1" -e "Total" -B 1 -A 2
