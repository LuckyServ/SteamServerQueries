#!/bin/bash
#
# Script to search a player in all the servers.
#
# Example: ./p lucky
# 
# Author: Luckylock

python3 steamGameServer_A2S_INFO.py ap < iplist 2> failedConnections | grep -i -e "\[.*$1.*\]" -e "Total Players" -B 4
