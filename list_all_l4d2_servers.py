#!/usr/bin/env python3.7
import valve.source.master_server

with valve.source.master_server.MasterServerQuerier(address=("hl2master.steampowered.com", 27011)) as msq:
    servers = msq.find(
        duplicates="skip",
        gamedir="left4dead2",
    )

    for host, port in servers:
        print("{}:{}".format(host, port))
