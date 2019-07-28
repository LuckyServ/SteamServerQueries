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
#    -p show player names
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

A2S_PLAYER = binascii.unhexlify("FFFFFFFF55FFFFFFFF")
A2S_PLAYER_START_INDEX = 6

STEAM_PACKET_SIZE = 1400
TIMEOUT = 0.5

isFirstLine = True

# Arguments handling (eh.. it'll do)
allArgs = ""
for i in range(1, len(sys.argv)):
    allArgs = allArgs + sys.argv[1]
isVerbose = "v" in allArgs
onlyActive = "a" in allArgs
onlyEmpty = "e" in allArgs
showPlayerNames = "p" in allArgs

if onlyEmpty and onlyActive:
    print("Option -e (only empty) and -a (only active) can't be used together.")
    raise SystemExit

# Gets string from data starting from index.
#
# @param data bytearray data from server response
# @param index position to start building the string
# @return (str, index) tuple where str is the built string and index the new position
def getString(data, index):
    strFromBytes = ""
    startIndex = index
    foundString = False

    # Assemble string until null byte is found
    while data[index] != 0:
        index += 1

    # There are sometimes decoding issues, just move up the start index
    # until it can decode properly.
    while not(foundString) and startIndex < index:
        try:
            strFromBytes = str(data[startIndex:index], "utf-8")
            foundString = True
        except UnicodeDecodeError: 
            startIndex += 1

    index += 1
    return strFromBytes, index

# Represents a single player information from A2S_PLAYER
class ValveA2SPlayer:
    def __init__(self):

        # Initialise
        self.index = -1
        self.name = ""
        self.score = -1
        self.duration = -1

    def __str__(self):
        return self.name

# Represents A2S_INFO
class ValveA2SInfo:
    def __init__(self, strServerIpPort): 

        # Initialise
        self.strServerIpPort = strServerIpPort
        self.dataIndex = A2S_INFO_START_INDEX
        self.pDataIndex = A2S_PLAYER_START_INDEX
        self.strServerName = ""
        self.strMapName = ""
        self.strFolder = ""
        self.strGame = ""
        self.numPlayers = -1
        self.strPlayers = ""
        self.numId = -1
        self.numMaxPlayers = -1
        self.numBots = -1
        self.strServerType = ""
        self.strEnvironment = ""
        self.strVisibility = ""
        self.strVAC = ""
        self.connect = False
        self.objPlayers = []
        self.numPlayersFromA2SPlayer = 0

    # Requests information from server and stores it in class variables.
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
            rawInfoData, addr = sock.recvfrom(STEAM_PACKET_SIZE)
            
            # Done
            self.data = bytearray(rawInfoData)
            self.getStrings()
            self.getNumericValues()

            if showPlayerNames and self.numPlayers > 0:
                # Get player list
                sock.sendto(A2S_PLAYER, (ipPortSplit[0], int(ipPortSplit[1])))
                rawPlayerData, addr = sock.recvfrom(STEAM_PACKET_SIZE)
                sock.sendto(bytearray(binascii.unhexlify("FFFFFFFF55")) + bytearray(rawPlayerData)[5:], (ipPortSplit[0], int(ipPortSplit[1])))
                rawPlayerData, addr = sock.recvfrom(STEAM_PACKET_SIZE)

                self.playerData = bytearray(rawPlayerData)
                self.getPlayerInfo()

            self.connect = True
            sock.close
        except socket.error:
            self.connect = False

    # Gets the string variables from the data
    def getStrings(self):
        self.strServerName, self.dataIndex = getString(self.data, self.dataIndex)
        self.strMapName, self.dataIndex = getString(self.data, self.dataIndex)
        self.strFolder, self.dataIndex = getString(self.data, self.dataIndex)
        self.strGame, self.dataIndex = getString(self.data, self.dataIndex)

    # Gets the numeric variables from the data
    def getNumericValues(self):
        i = self.dataIndex
        data = self.data
        self.numId = (data[i]) + (data[i+1] << 8)
        self.numPlayers = data[i+2]
        self.numMaxPlayers = data[i+3]
        self.numBots = data[i+4]
        self.strServerType = (
            "dedicated server" if chr(data[i+5]) == 'd' 
            else "non-dedicated server" if chr(data[i+5]) == 'l' 
            else "SourceTV relay (proxy)"
        )
        self.strEnvironment = (
            "Linux" if chr(data[i+6]) == 'l' 
            else "Windows" if chr(data[i+6]) == 'w' 
            else "Mac"
        )
        self.strVisibility = "private" if data[i+7] else "public"
        self.strVAC = "secured" if data[i+8] else "unsecured"

    # Creates player objects and parses the player data
    def getPlayerInfo(self):
        n = 0
        self.numPlayersFromA2SPlayer = self.playerData[self.pDataIndex]
        self.pDataIndex += 1
        while self.pDataIndex < len(self.playerData):
            self.objPlayers.append(ValveA2SPlayer())
            self.objPlayers[n].index = self.playerData[self.pDataIndex]
            self.objPlayers[n].name, self.pDataIndex = getString(self.playerData, self.pDataIndex + 1)
            self.objPlayers[n].score = (
                self.playerData[self.pDataIndex] 
                + (self.playerData[self.pDataIndex + 1] << 8) 
                + (self.playerData[self.pDataIndex + 2] << 16) 
                + (self.playerData[self.pDataIndex + 3] << 24)
            )
            self.pDataIndex = self.pDataIndex + 8
            n += 1

    def __str__(self):
        if self.connect:
            s = (
                "Server".ljust(LJUST_VALUE) + FIELD_SEP + self.strServerIpPort + "\n" 
                + "Name".ljust(LJUST_VALUE) + FIELD_SEP + self.strServerName + "\n"
                + "Map".ljust(LJUST_VALUE) + FIELD_SEP + self.strMapName + "\n"
                + "Players".ljust(LJUST_VALUE) + FIELD_SEP + str(self.numPlayers) + "\n"
            )

            if isVerbose:
                s += (
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

            if showPlayerNames and self.numPlayers > 0:
                s += str(list(map(str, self.objPlayers))) + "\n"

        else:
            s = (
                "Server".ljust(LJUST_VALUE) + FIELD_SEP + self.strServerIpPort + "\n"
                + " " * LJUST_VALUE + "   CONNECTION FAILED" + "\n"
            )

        return s

def thread_a2sInfo_getMembers(objA2sInfo):
    objA2sInfo.getMembers()

# Prepare threads
totalPlayers = 0
i = 0
a2sInfoArray = []
threads = []
for ipPort in sys.stdin:
    ipPort = ipPort.strip()
    if len(ipPort) < 10 or ipPort[0] == "#": continue
    a2sInfoArray.append(ValveA2SInfo(ipPort))
    threads.append(threading.Thread(target=thread_a2sInfo_getMembers, args=(a2sInfoArray[i],)))
    i += 1

# Launch threads
for t in threads:
    t.start()
for t in threads:
    t.join()

# Print server information
for serverInfo in a2sInfoArray:
    if ((not(onlyActive) or serverInfo.numPlayers > 0) and (not(onlyEmpty) or serverInfo.numPlayers <= 0)): 
        if serverInfo.connect: totalPlayers = totalPlayers + serverInfo.numPlayers
        print(serverInfo)

print("Total Players: " + str(totalPlayers))
