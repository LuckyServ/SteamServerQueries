#!/bin/bash
#
# Script to get empty servers filtered by list of names.
#
# Example: ./e chi
# 
# Author: Luckylock

names=""

for arg in "$@"
do
    names="$names -n $arg"
done

python3 steamGameServer_A2S_INFO.py -e $names < compList
