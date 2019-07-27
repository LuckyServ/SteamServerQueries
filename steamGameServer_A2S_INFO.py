#!/usr/bin/env python3
#
# Python script to make A2S_INFO queries to steam game servers.
#
# Arguments: -v for verbose output
#
# Author: Luckylock
#
# For documentation on steam game server queries, check
# https://developer.valvesoftware.com/wiki/Server_queries

import socket
import sys
import binascii

# List of servers to query
IP_PORT = ([
    "192.223.24.83:27015", 
    "192.223.30.176:27015", 
    "140.82.26.135:27015",
])

# Formatting
LINE_SEP = "----------------------------------------"
FIELD_SEP = " : "
LJUST_VALUE = 11 

# A2S_INFO values from Valve documentation
A2S_INFO = binascii.unhexlify("FFFFFFFF54536F7572636520456E67696E6520517565727900")
A2S_INFO_START_INDEX = 6
A2S_INFO_STRING_ARRAY = ( 
    ["Name", "Map", "Folder", "Game"]
)

STEAM_PACKET_SIZE = 1400
TIMEOUT = 0.5

# Prints a string from the UDP packet recieved by the steam server.
#
# @param infoName the info name of the string
# @param data the udp packet bytearray data
# @param i start index of the string
# @return start index of the next info
def printInfo(infoName, data, i):
    strFromBytes = ""

    # Assemble string until null byte is found
    while data[i] != 0:
        strFromBytes = strFromBytes + chr(data[i])
        i = i + 1

    # Print the string value
    if not(not(isVerbose) and (infoName == "Folder" or infoName == "Game")):
        print(infoName.ljust(LJUST_VALUE) + FIELD_SEP + strFromBytes)
    i = i + 1

    return i

isVerbose = len(sys.argv) >= 2 and sys.argv[1] == "-v"

print(LINE_SEP)

# Iterate over all IP addresses to print their A2S_INFO values
for ipPort in IP_PORT:
    print("Server".ljust(LJUST_VALUE) + FIELD_SEP + ipPort)

    # Send A2S_INFO request and get response from steam game server
    try:
        ipPortSplit = ipPort.split(":")

        # Prep socket for UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Don't wait forever for a response
        sock.settimeout(TIMEOUT)

        # Send steam game server request
        sock.sendto(A2S_INFO, (ipPortSplit[0], int(ipPortSplit[1])))

        # Get answer from server
        data, addr = sock.recvfrom(STEAM_PACKET_SIZE)

        # Done
        sock.close
    except:
        print(" " * LJUST_VALUE + "   CONNECTION FAILED")
        print(LINE_SEP)
        continue

    data = bytearray(data)

    # Print strings
    i = A2S_INFO_START_INDEX
    for infoName in A2S_INFO_STRING_ARRAY:
        i = printInfo(infoName, data, i)

    # Print numeric values
    print(
        "Players".ljust(LJUST_VALUE) + FIELD_SEP 
        + str(data[i+2])
    )

    if isVerbose: 
        print(
            "ID".ljust(LJUST_VALUE) + FIELD_SEP 
            + str((data[i]) + (data[i+1] << 8))
        )
        print(
            "Max Players".ljust(LJUST_VALUE) + FIELD_SEP 
            + str(data[i+3])
        )
        print(
            "Bots".ljust(LJUST_VALUE) + FIELD_SEP 
            + str(data[i+4])
        )
        print(
            "Server type".ljust(LJUST_VALUE) + FIELD_SEP 
            + ("dedicated server" if chr(data[i+5]) == 'd' else "non-dedicated server" if chr(data[i+5]) == 'l' else "SourceTV relay (proxy)")
        )
        print(
            "Environment".ljust(LJUST_VALUE) + FIELD_SEP 
            + ("Linux" if chr(data[i+6]) == 'l' else "Windows" if chr(data[i+6]) == 'w' else "Mac")
        )
        print(
            "Visibility".ljust(LJUST_VALUE) + FIELD_SEP 
            + ("private" if data[i+7] else "public")
        )
        print(
            "VAC".ljust(LJUST_VALUE) + FIELD_SEP 
            + ("secured" if data[i+8] else "unsecured")
        )

    print(LINE_SEP)
