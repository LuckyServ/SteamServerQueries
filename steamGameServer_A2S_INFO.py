#!/usr/bin/env python3
#
# Python script to make A2S_INFO queries to steam game servers.
#
# It reads the server list to query from stdin, each line has to be ip:port.
#
# Example input file:
#
# 192.223.24.83:27015
# 192.223.30.176:27015
# 140.82.26.135:27015
#
# Arguments: 
#    -v for verbose output
#    -a for only active servers
#    -e for only empty servers
#
# Author: Luckylock
#
# For documentation on steam game server queries, check
# https://developer.valvesoftware.com/wiki/Server_queries

import socket
import sys
import binascii
import threading

# Formatting
LINE_SEP = "----------------------------------------"
FIELD_SEP = " : "
LJUST_VALUE = 11 

# A2S_INFO values from Valve documentation
A2S_INFO = binascii.unhexlify("FFFFFFFF54536F7572636520456E67696E6520517565727900")
A2S_INFO_START_INDEX = 6

STEAM_PACKET_SIZE = 1400
TIMEOUT = 0.5

isFirstLine = True

# Arguments handling
allArgs = ""
for i in range(1, len(sys.argv)):
    allArgs = allArgs + sys.argv[1]
isVerbose = "v" in allArgs
onlyActive = "a" in allArgs
onlyEmpty = "e" in allArgs

class ValveA2SInfo:
    def __init__(self, strServerIpPort): 

        # Initialise
        self.strServerIpPort = strServerIpPort
        self.dataIndex = A2S_INFO_START_INDEX
        self.strServerName = ""
        self.strMapName = ""
        self.strFolder = ""
        self.strGame = ""
        self.numPlayers = -1
        self.numId = -1
        self.numMaxPlayers = -1
        self.numBots = -1
        self.strServerType = ""
        self.strEnvironment = ""
        self.strVisibility = ""
        self.strVAC = ""
        self.connect = False

    def getMembers(self):
        # Send A2S_INFO request and get response from steam game server
        try:
            ipPortSplit = self.strServerIpPort.split(":")

            # Prep socket for UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Don't wait forever for a response
            sock.settimeout(TIMEOUT)

            # Send steam game server request
            sock.sendto(A2S_INFO, (ipPortSplit[0], int(ipPortSplit[1])))

            # Get answer from server
            rawData, addr = sock.recvfrom(STEAM_PACKET_SIZE)

            # Done
            sock.close
            self.data = bytearray(rawData)
            self.getStrings()
            self.getNumericValues()
            self.connect = True
        except:
            self.connect = False

    def getStrings(self):
        self.strServerName = self.getString()
        self.strMapName = self.getString()
        self.strFolder = self.getString()
        self.strGame = self.getString()

    def getString(self):
        strFromBytes = ""

        # Assemble string until null byte is found
        while self.data[self.dataIndex] != 0:
            strFromBytes = strFromBytes + chr(self.data[self.dataIndex])
            self.dataIndex = self.dataIndex + 1

        self.dataIndex = self.dataIndex + 1
        return strFromBytes

    def getNumericValues(self):
        i = self.dataIndex
        data = self.data
        self.numId = (data[i]) + (data[i+1] << 8)
        self.numPlayers = data[i+2]
        self.numMaxPlayers = data[i+3]
        self.numBots = data[i+4]
        self.strServerType = "dedicated server" if chr(data[i+5]) == 'd' else "non-dedicated server" if chr(data[i+5]) == 'l' else "SourceTV relay (proxy)"
        self.strEnvironment = "Linux" if chr(data[i+6]) == 'l' else "Windows" if chr(data[i+6]) == 'w' else "Mac"
        self.strVisibility = "private" if data[i+7] else "public"
        self.strVAC = "secured" if data[i+8] else "unsecured"

    def __str__(self):
        s = (
            "Server".ljust(LJUST_VALUE) + FIELD_SEP + self.strServerIpPort + "\n" 
            + "Name".ljust(LJUST_VALUE) + FIELD_SEP + self.strServerName + "\n"
            + "Map".ljust(LJUST_VALUE) + FIELD_SEP + self.strMapName + "\n"
            + "Players".ljust(LJUST_VALUE) + FIELD_SEP + str(self.numPlayers) + "\n"
        )

        if isVerbose:
            s = s + (
                "Game".ljust(LJUST_VALUE) + FIELD_SEP + self.strGame + "\n"
                + "Folder".ljust(LJUST_VALUE) + FIELD_SEP + self.strFolder + "\n"
                + "ID".ljust(LJUST_VALUE) + FIELD_SEP + str(self.numId) + "\n"
                + "Max Players".ljust(LJUST_VALUE) + FIELD_SEP + str(self.numMaxPlayers) + "\n"
                + "Bots".ljust(LJUST_VALUE) + FIELD_SEP + str(self.numBots) + "\n"
                + "Server type".ljust(LJUST_VALUE) + FIELD_SEP + self.strServerType + "\n"
                + "Environment".ljust(LJUST_VALUE) + FIELD_SEP + self.strEnvironment + "\n"
                + "Visibility".ljust(LJUST_VALUE) + FIELD_SEP + self.strVisibility + "\n"
                + "VAC".ljust(LJUST_VALUE) + FIELD_SEP + self.strVAC + "\n"
            )

        return s

i = 0
for ipPort in sys.stdin:
    a2sInfoArray(i) = ValveA2SInfo(ipPort.strip())

