#!/usr/bin/env python2.7
#
# Python script to make A2S_INFO queries to steam game servers.
#
# Author: Luckylock
#
# For documentation on steam game server queries, check
# https://developer.valvesoftware.com/wiki/Server_queries

import socket

IP_PORT = ([
    "192.223.24.83:27015", 
    "192.223.30.176:27015", 
    "140.82.26.135:27015",
])

LINE_SEP = "----------------------------------------"
LJUST_VALUE = 11 

A2S_INFO = "FFFFFFFF54536F7572636520456E67696E6520517565727900".decode("hex")
A2S_INFO_START_INDEX = 6
A2S_INFO_STRING_ARRAY = ( 
    ["Name", "Map", "Folder", "Game"]
)

# Prints a string from the UDP packet recieved by the steam server.
#
# @param infoName the info name of the string
# @param data the udp packet bytearray data
# @param i start index of the string
# @return start index of the next info
def printInfo(infoName, data, i):
    strFromBytes = ""
    while data[i] != 0:
        strFromBytes = strFromBytes + chr(data[i])
        i = i + 1
    if infoName != "Folder" and infoName != "Game":
        print(infoName.ljust(LJUST_VALUE) + " : " + strFromBytes)
    i = i + 1
    return i

print(LINE_SEP)

# Iterate over all IP addresses to print their A2S_INFO values
for ipPort in IP_PORT:
    print("Server".ljust(LJUST_VALUE) + " : " + ipPort)

    # Send A2S_INFO request and get response from steam game server
    try:
        ipPortSplit = ipPort.split(":")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.5)
        sock.sendto(A2S_INFO, (ipPortSplit[0], int(ipPortSplit[1])))
        data, addr = sock.recvfrom(1024)
        sock.close
    except:
        print(" " * LJUST_VALUE + "   CONNECTION FAILED")
        print(LINE_SEP)
        continue

    # Convert data to bytearray 
    data = bytearray(data)

    # Print the strings
    i = A2S_INFO_START_INDEX
    for infoName in A2S_INFO_STRING_ARRAY:
        i = printInfo(infoName, data, i)

    # Print the numeric values
    print("ID".ljust(LJUST_VALUE) + " : " + str((data[i]) + (data[i+1] << 8)))
    print("Players".ljust(LJUST_VALUE) + " : " + str(data[i+2]))
    print("Max Players".ljust(LJUST_VALUE) + " : " + str(data[i+3]))
    print("Bots".ljust(LJUST_VALUE) + " : " + str(data[i+4]))
    print("Server type".ljust(LJUST_VALUE) + " : " + ("dedicated server" if chr(data[i+5]) == 'd' else "non-dedicated server" if chr(data[i+5]) == 'l' else "SourceTV relay (proxy)"))
    print("Environment".ljust(LJUST_VALUE) + " : " + ("Linux" if chr(data[i+6]) == 'l' else "Windows" if chr(data[i+6]) == 'w' else "Mac"))
    print("Visibility".ljust(LJUST_VALUE) + " : " + ("private" if data[i+7] else "public"))
    print("VAC".ljust(LJUST_VALUE) + " : " + ("secured" if data[i+8] else "unsecured"))
    print(LINE_SEP)
