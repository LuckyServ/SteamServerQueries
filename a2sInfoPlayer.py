#!/usr/bin/env python3
#
# Python script to make A2S_INFO and A2S_PLAYER requests to steam game servers.
#
# It reads the server list to query from stdin, each line has to be ip:port.
#
# Example input file:
#
# 192.223.24.83:27015
# 192.223.30.176:27015
# 140.82.26.135:27015
#
# Failed connections are logged in the failedConnections file.
#
# usage: steamGameServer_A2S_INFO.py -h
#
# Author: Luckylock
#
# For documentation on steam game server queries, check
# https://developer.valvesoftware.com/wiki/Server_queries

import socket
import sys
import binascii
import threading
import time
import argparse
import re

# Maximum number of threads alive at once
MAX_THREAD_COUNT = 32

# Error number for too many files (when too many threads are alive at once)
TOO_MANY_OPEN_FILES = 24

# Formatting
LINE_SEP = "----------------------------------------"
FIELD_SEP = " : "
LJUST_VALUE = 11 
maxNameLength = 10
maxMapLength = 10

# A2S values from Valve documentation
A2S_INFO = binascii.unhexlify("FFFFFFFF54536F7572636520456E67696E6520517565727900")
A2S_INFO_START_INDEX = 6
A2S_PLAYER = binascii.unhexlify("FFFFFFFF55FFFFFFFF")
A2S_PLAYER_START_INDEX = 5

# UPD packet parameters
STEAM_PACKET_SIZE = 1400

# These can be ajusted through command line arguments
TIMEOUT = 300
RETRY = 1

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
        self.strServerIpPort = strServerIpPort
        self.initialise()

    def initialise(self):
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
        self.ping = 1000

    # Requests information from server and stores it in class variables.
    def getMembers(self):
        socketRetries = 0
        
        # UDP packets can be unreliable, so request as many times as needed.
        while not(self.connect) and socketRetries < retry:
            socketRetries += 1
            self.initialise()

            # Send A2S_INFO request and get response from steam game server
            try:
                ipPortSplit = self.strServerIpPort.split(":")

                # Prep socket for UDP
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                # Don't wait forever for a response
                sock.settimeout(timeout / 1000)

                # Calculate start time (for ping)
                startTime = time.time()

                # Send steam game server request
                sock.sendto(A2S_INFO, (ipPortSplit[0], int(ipPortSplit[1])))

                # Get answer from server
                rawInfoData, addr = sock.recvfrom(STEAM_PACKET_SIZE)

                # We got data from another IP:PORT, this one doesn't count
                if "{}:{}".format(addr[0], addr[1]) != self.strServerIpPort: 
                    socketRetries -= 1
                    continue

                self.ping = (time.time() - startTime) * 1000
                
                # Done
                self.data = bytearray(rawInfoData)
                self.getStrings()
                self.getNumericValues()

                if showPlayers and self.numPlayers > 0:
                    # Get player list
                    sock.sendto(A2S_PLAYER, (ipPortSplit[0], int(ipPortSplit[1])))
                    rawPlayerData, addr = sock.recvfrom(STEAM_PACKET_SIZE)
                    sock.sendto(bytearray(binascii.unhexlify("FFFFFFFF55")) 
                        + bytearray(rawPlayerData)[5:], (ipPortSplit[0], int(ipPortSplit[1])))
                    rawPlayerData, addr = sock.recvfrom(STEAM_PACKET_SIZE)

                    self.playerData = bytearray(rawPlayerData)
                    self.getPlayerInfo()

                self.connect = True
                sock.close()
            except socket.error as e:
                if e.errno == TOO_MANY_OPEN_FILES:
                    print(
                        "Too many threads, reduce the max thread count with "
                        + "option --threadcount or increase max open files "
                        + "(ulimit -n). Current threadcount value is {}."
                        .format(maxThreadCount), file=sys.stderr
                    )
                elif "timed out" not in str(e) and "service not know" not in str(e):
                    print("{} : {}".format(str(e), self.strServerIpPort), file=sys.stderr)
                self.connect = False
                sock.close()

    # Gets the string variables from the data
    def getStrings(self):
        global maxNameLength
        global maxMapLength

        self.strServerName, self.dataIndex = getString(self.data, self.dataIndex)
        self.strMapName, self.dataIndex = getString(self.data, self.dataIndex)
        self.strFolder, self.dataIndex = getString(self.data, self.dataIndex)
        self.strGame, self.dataIndex = getString(self.data, self.dataIndex)

        maxNameLength = max(maxNameLength, len(self.strServerName) + 2)
        maxMapLength = max(maxMapLength, len(self.strMapName) + 2)

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
        while self.pDataIndex + 3 < len(self.playerData):
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
                self.strServerName.ljust(maxNameLength)
                + self.strServerIpPort.ljust(23)
                + (str(int(self.ping)).rjust(3) + " ms").ljust(8)
                + self.strMapName.ljust(maxMapLength)
                + str(self.numPlayers).rjust(3)
            )

            if showPlayers: s += "\n"

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

            if showPlayers and self.numPlayers > 0:
                s += str(list(map(str, self.objPlayers))) + "\n"

        else:
            s = (
                "Server".ljust(LJUST_VALUE) + FIELD_SEP + self.strServerIpPort + "\n"
                + " " * LJUST_VALUE + "   CONNECTION FAILED" + "\n"
            )

        return s
   
    # Determines if self should print based on cli.
    def shouldPrint(self):
        # Only active and active logic
        p = (
            (onlyActive and serverInfo.numPlayers > 0) 
            or (onlyEmpty and serverInfo.numPlayers == 0) 
            or (not(onlyActive) and not(onlyEmpty))
        ) 

        # Minimum player count
        if p and minPlayerCount != None:
            p = p and self.numPlayers >= minPlayerCount

        # Maximum player count
        if p and maxPlayerCount != None:
            p = p and self.numPlayers <= maxPlayerCount

        # Search for server name
        if p and searchNames != None:
            p = p and (
                True in map(lambda argName: argName.lower() in self.strServerName.lower(), searchNames)     
            )

        # Search for player
        if p and searchPlayers != None:
            playerFound = self.numPlayers > 0

            if playerFound:
                for player in self.objPlayers:
                    playerFound = (
                        True in map(lambda argPlayer: argPlayer.lower() in player.name.lower(), searchPlayers)
                    )
                    if playerFound: break

            p = p and playerFound

        return p

# Handler function to call for each thread.
#
# objA2sInfoArray array of A2s objects to process
def thread_a2sInfo_getMembers(objA2sInfoArray):
    for sInfo in objA2sInfoArray:
        sInfo.getMembers()

# Write to output file the iplist passed in.
#
# @outputFile the destination output file name
# @ipList the list of ip:port
def writeOutputFile(outputFile, ipList):
    f = open(outputFile, "w")
    for ipPort in ipList:
        f.write(ipPort + "\n")
    f.close()

##############
# SCRIPT START
##############

# Arguments handling
SORT_FIELD_CHOICES = ['name', 'ip', 'ping', 'map', 'player']
SORT_FIELD_ATTR = ['strServerName', 'strServerIpPort', 'ping', 'strMapName', 'numPlayers']

parser = argparse.ArgumentParser(description=(
        "Make A2S_INFO and A2S_PLAYER requests to steam game servers. "
        + "The ip:port list is read from stdin."
    )
)

parser.add_argument("-a", "--active", action='store_true', help="only show active servers")
parser.add_argument("-e", "--empty", action='store_true', help="only show empty servers")
parser.add_argument("-v", "--verbose", action='store_true', help="verbose information")
parser.add_argument("-s", "--showplayers", action='store_true', help="show players")
parser.add_argument("-n", "--name", action='append', help="search for server name, accepts multiple values (disjunction)")
parser.add_argument("-p", "--player", action='append', help="search for player, accepts multiple values (disjunction)")
parser.add_argument("-m", "--minplayer", type=int, help="minimum player count (inclusive)")
parser.add_argument("-x", "--maxplayer", type=int, help="maximum player count (inclusive)")
parser.add_argument("-t", "--timeout", type=float, help="timeout before retry (ms)", default=TIMEOUT)
parser.add_argument("-r", "--retry", type=int, help="request retry amount", default=RETRY)
parser.add_argument("-c", "--threadcount", type=int, help="max requests at once (MAX_THREAD_COUNT)", default=MAX_THREAD_COUNT)
parser.add_argument("-o", "--outputfilesuccess", help="output destination file for successful connections")
parser.add_argument("-f", "--outputfilefailed", help="output destination file for failed connections")
parser.add_argument("-w", "--outputfileshow", help="output destination file for showing connections")
parser.add_argument("--sort", help="sort by field", choices=SORT_FIELD_CHOICES, default="ping")
parser.add_argument("--sortreverse", action='store_true', help="reverse sort", default=False)
parser.add_argument("--printestimate", action='store_true', help="prints an estimate of how long the script will run", default=False)

parsedArgs = parser.parse_args()

onlyEmpty = parsedArgs.empty
onlyActive = parsedArgs.active
searchNames = parsedArgs.name
searchPlayers = parsedArgs.player
isVerbose = parsedArgs.verbose
showPlayers = parsedArgs.showplayers or searchPlayers != None
minPlayerCount = parsedArgs.minplayer
maxPlayerCount = parsedArgs.maxplayer
timeout = parsedArgs.timeout
retry = parsedArgs.retry
maxThreadCount = parsedArgs.threadcount
outputFileSuccess = parsedArgs.outputfilesuccess
outputFileFailed = parsedArgs.outputfilefailed
outputFileShow = parsedArgs.outputfileshow
sortBy = parsedArgs.sort
sortReverse = parsedArgs.sortreverse
printEstimate = parsedArgs.printestimate

# Invalid arguments combination
invalidArgs = False
if onlyEmpty and onlyActive:
    print("Option --empty and --active can't be used together.", file=sys.stderr)
    invalidArgs = True

if timeout <= 0:
    print("Option --timeout must be positive.", file=sys.stderr) 
    invalidArgs = True

if retry <= 0:
    print("Option --retry must be positive.", file=sys.stderr)
    invalidArgs = True

if maxThreadCount <= 0:
    print("Option --threadcount must be positive.", file=sys.stderr)
    invalidArgs = True

if invalidArgs:
    raise SystemExit

# Prepare a2sInfoArray
a2sInfoArray = []
for ipPort in sys.stdin:
    ipPort = ipPort.strip()

    # Basic IP:PORT validation
    if re.search("^(([0-9]{1,3})\.){3}[0-9]{1,3}:[0-9]{1,5}$", ipPort) != None:
        a2sInfoArray.append(ValveA2SInfo(ipPort))

# Print how much time it will take to process
if printEstimate:
    processTime = len(a2sInfoArray) / maxThreadCount * (timeout / 1000) * retry
    print(
        "Sending {} requests, it will take about {} seconds...\n"
        .format(len(a2sInfoArray), round(processTime, 2))
    )

startTime = time.time()

# Make threads and assign them a2sInfoPerThread
threads = []
a2sInfoPerThread = len(a2sInfoArray) / maxThreadCount
for i in range(0, maxThreadCount):
    beginIndex = int(a2sInfoPerThread * i)
    if i == maxThreadCount -1:
        endIndex = len(a2sInfoArray)
    else:
        endIndex = int(min(a2sInfoPerThread * (i + 1), len(a2sInfoArray)))
    threads.append(
        threading.Thread(target=thread_a2sInfo_getMembers, 
        args=(a2sInfoArray[beginIndex:endIndex],))
    )

# Launch threads
for t in threads:
    t.start()
for t in threads:
    t.join()

# Print server information
totalPlayers = 0
failedConnectCount = 0
successConnectCount = 0
showConnectCount = 0
failedConnectList = []
successfulConnectList = []
showConnectList = []
for serverInfo in (sorted(a2sInfoArray, 
        key = lambda x: getattr(x, SORT_FIELD_ATTR[SORT_FIELD_CHOICES.index(sortBy)]), reverse=sortReverse)):

    if serverInfo.connect:
        successConnectCount += 1
        successfulConnectList.append(serverInfo.strServerIpPort)
        if serverInfo.numPlayers >= 0 and serverInfo.shouldPrint(): 
            showConnectCount += 1
            showConnectList.append(serverInfo.strServerIpPort)
            totalPlayers = totalPlayers + serverInfo.numPlayers
            print(serverInfo)
    else:
        failedConnectList.append(serverInfo.strServerIpPort)
        failedConnectCount += 1

# Write ip:port results to files
if outputFileFailed != None and failedConnectCount > 0:
    writeOutputFile(outputFileFailed, failedConnectList)
if outputFileSuccess != None and successConnectCount > 0:
    writeOutputFile(outputFileSuccess, successfulConnectList)
if outputFileShow != None and showConnectCount > 0:
    writeOutputFile(outputFileShow, showConnectList)

endTime = time.time()
totalTime = "{} seconds".format(round(endTime - startTime, 2))

# Print summary
if not(showPlayers) and not(isVerbose): print()
print(
    "Total Players: " + str(totalPlayers) 
    + (" ({} showing, {} successful, {} failed, {} total) in {}"
    .format(showConnectCount, successConnectCount, failedConnectCount, len(a2sInfoArray), totalTime))
)
