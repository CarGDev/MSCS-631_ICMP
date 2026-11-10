# Python ICMP Ping Client

# Project Information

- **Project:** Python Lab 4 - ICMP
- **Name:** Carlos Gutierrez
- **Email:** cgutierrez44833@ucumberlands.edu
- **Course:** MSCS-631-B01 Advanced Computer Networks
- License: MIT

## Usage

### Run

Raw sockets need root privileges:

```bash
sudo python3 src/icmp.py <host> <timeout> <count>
```

- `host`: hostname or IP address to ping
- `timeout`: seconds to wait for each reply (must be greater than 0)
- `count`: number of echo requests to send (must be greater than 0)

Example:

```bash
sudo python3 src/icmp.py google.com 1 4
```

### Example output

This output is illustrative. Your addresses and times will differ.

```text
Pinging google.com (142.250.72.14) using Python:

1: 36 bytes from 142.250.72.14: icmp_seq=1 ttl=117 time=14.512 ms
2: 36 bytes from 142.250.72.14: icmp_seq=1 ttl=117 time=13.870 ms
3: Request timed out.
4: 36 bytes from 142.250.72.14: icmp_seq=1 ttl=117 time=15.004 ms

--- Ping Statistics ---
4 packets transmitted, 3 received, 25.0% packet loss
rtt min/avg/max = 13.870/14.462/15.004 ms
```

### How it works

- `checksum`: computes the ICMP checksum over the header and data
- `sendOnePing`: builds an Echo Request (type 8) with the send time as payload and sends it
- `receiveOnePing`: waits with `select`, reads the reply, checks type, code and ID, then computes the RTT
- `doOnePing`: opens a raw ICMP socket, sends one ping and returns the result
- `ping`: reads the arguments, loops `count` times at about one per second and handles Ctrl+C
- `printStatistics`: prints packets sent and received, loss percentage and RTT min/avg/max

### Notes

- Root privileges are required for raw sockets
- Some hosts and networks block ICMP, so a timeout does not always mean the host is down
- Missing or invalid arguments print the usage message and exit
- Press Ctrl+C to stop early. The statistics are still printed

## About

Course assignment for MSCS-631 implementing ICMP ping with Python raw sockets.
