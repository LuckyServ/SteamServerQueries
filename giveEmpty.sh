#!/bin/bash
#
# Script to get empty servers in location of choice.
#
# Location is specified in the first argument.
#
# Author: Luckylock

./steamGameServer_A2S_INFO.py < iplist e | grep -i "$1" -B 1 -A 2
