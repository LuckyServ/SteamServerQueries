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

eval "python3 steamGameServer_A2S_INFO.py -sa $names < compList"
