#!/bin/bash
#
# Script to search for a list of players in all the servers.
#
# Example: ./p lucky bob
# 
# Author: Luckylock

names=""

for arg in "$@"
do
    names="$names -p $arg"
done

python3 steamGameServer_A2S_INFO.py -a $names < compList
