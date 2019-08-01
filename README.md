# Steam Game Server Queries

This python script requests information from steam game servers. So far, this
has only been tested on competitive L4D2 servers.

This python script takes a list of IP:PORT steam servers from stdin and
outputs information about the server (A2S_INFO and A2S_PLAYER).

To get started, just clone the repository. Since the script reads from stdin,
just redirect your list of IP:PORT like so:

```bash
 $ ./a2sInfoPlayer.py < serverlist/compList 
SirPlease NY #1 | Zonemod v1.9.4           192.223.24.99:27015     25 ms  c5m1_waterfront            10
SirPlease NY #3                            192.223.24.99:27017     26 ms  c2m1_highway                0
Asylum NY T100 #1 | Zonemod v1.9.3         192.223.24.187:27015    28 ms  c2m3_coaster                1
[2] Larry's L4D2 Realism                   104.153.108.80:27016    31 ms  c1m3_mall                   0
SirPlease CHI #2                           74.91.122.107:27016     31 ms  c2m1_highway                0
SirPlease NY #2 | Zone :X: Skeet           192.223.24.99:27016     32 ms  c2m2_fairgrounds            1
[...]
```

There are many command line options available, here's the help page:

```bash
 $ ./a2sInfoPlayer.py -h
usage: a2sInfoPlayer.py [-h] [-a] [-e] [-v] [-s] [-n NAME] [-p PLAYER]
                        [-m MINPLAYER] [-x MAXPLAYER] [-t TIMEOUT] [-r RETRY]
                        [-c THREADCOUNT] [-o OUTPUTFILESUCCESS]
                        [-f OUTPUTFILEFAILED] [-w OUTPUTFILESHOW]
                        [--sort {name,ip,ping,map,player}] [--sortreverse]
                        [--printestimate]

Make A2S_INFO and A2S_PLAYER requests to steam game servers. The ip:port list
is read from stdin.

optional arguments:
  -h, --help            show this help message and exit
  -a, --active          only show active servers
  -e, --empty           only show empty servers
  -v, --verbose         verbose information
  -s, --showplayers     show players
  -n NAME, --name NAME  search for server name, accepts multiple values
                        (disjunction)
  -p PLAYER, --player PLAYER
                        search for player, accepts multiple values
                        (disjunction)
  -m MINPLAYER, --minplayer MINPLAYER
                        minimum player count (inclusive)
  -x MAXPLAYER, --maxplayer MAXPLAYER
                        maximum player count (inclusive)
  -t TIMEOUT, --timeout TIMEOUT
                        timeout before retry (ms)
  -r RETRY, --retry RETRY
                        request retry amount
  -c THREADCOUNT, --threadcount THREADCOUNT
                        max requests at once (MAX_THREAD_COUNT)
  -o OUTPUTFILESUCCESS, --outputfilesuccess OUTPUTFILESUCCESS
                        output destination file for successful connections
  -f OUTPUTFILEFAILED, --outputfilefailed OUTPUTFILEFAILED
                        output destination file for failed connections
  -w OUTPUTFILESHOW, --outputfileshow OUTPUTFILESHOW
                        output destination file for showing connections
  --sort {name,ip,ping,map,player}
                        sort by field
  --sortreverse         reverse sort
  --printestimate       prints an estimate of how long the script will run
```
