import os
import select
import struct
import sys
import time
from socket import *

ICMP_ECHO_REQUEST = 8


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xFFFFFFFF
        count = count + 2
    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xFFFFFFFF
    csum = (csum >> 16) + (csum & 0xFFFF)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xFFFF
    answer = answer >> 8 | (answer << 8 & 0xFF00)
    return answer


rtt_min = float("+inf")
rtt_max = float("-inf")
rtt_sum = 0
rtt_cnt = 0
cnt = 0


def printStatistics(sent, received, rtt_min, rtt_max, rtt_sum):
    lost = sent - received
    loss_percentage = (lost / sent) * 100 if sent > 0 else 0

    print("\n--- Ping Statistics ---")
    print(
        f"{sent} packets transmitted, {received} received, "
        f"{loss_percentage:.1f}% packet loss"
    )

    if received > 0:
        print(
            f"rtt min/avg/max = "
            f"{rtt_min:.3f}/"
            f"{rtt_sum / received:.3f}/"
            f"{rtt_max:.3f} ms"
        )


def receiveOnePing(mySocket: socket, ID, timeout):
    global rtt_min, rtt_max, rtt_sum, rtt_cnt
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = time.time() - startedSelect
        if whatReady[0] == []:  # Timeout
            return "Request timed out."
        timeReceived = time.time()
        recPacket, _ = mySocket.recvfrom(1024)

        # Fill in start
        # Fetch the ICMP header from the IP packet

        type, code, _, id, seq = struct.unpack("bbHHh", recPacket[20:28])
        if type != 0:
            return "Expected type=0, but got {}".format(type)
        if code != 0:
            return "Expected code=0, but got {}".format(code)
        if ID != id:
            return "Expected id={}, but got {}".format(ID, id)

        (send_time,) = struct.unpack("d", recPacket[28:36])
        rtt = (timeReceived - send_time) * 1000
        rtt_cnt += 1
        rtt_sum += rtt
        rtt_min = min(rtt_min, rtt)
        rtt_max = max(rtt_max, rtt)

        ip_header = struct.unpack("!BBHHHBBH4s4s", recPacket[:20])
        ttl = ip_header[5]
        saddr = inet_ntoa(ip_header[8])
        length = len(recPacket) - 20

        # Fill in end
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."

        return "{} bytes from {}: icmp_seq={} ttl={} time={:.3f} ms".format(
            length, saddr, seq, ttl, rtt
        )


def sendOnePing(mySocket, destAddr, ID):
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    myChecksum = checksum(header + data)
    myChecksum = htons(myChecksum) & 0xFFFF

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    mySocket = socket(AF_INET, SOCK_RAW, icmp)
    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout)
    mySocket.close()
    return delay


def ping():
    global rtt_min, rtt_max, rtt_sum, rtt_cnt

    try:
        host = sys.argv[1]
        timeout = float(sys.argv[2])
        times = int(sys.argv[3])

        if timeout <= 0 or times <= 0:
            raise ValueError

    except (IndexError, ValueError):
        print("Usage: sudo python3 src/icmp.py <host> <timeout> <count>")
        sys.exit(1)

    dest = gethostbyname(host)

    print(f"Pinging {host} ({dest}) using Python:\n")

    # Reset statistics
    rtt_min = float("+inf")
    rtt_max = float("-inf")
    rtt_sum = 0
    rtt_cnt = 0

    sent = 0

    try:
        for i in range(times):
            start = time.monotonic()
            sent += 1

            delay = doOnePing(dest, timeout)
            print(f"{i + 1}: {delay}")

            elapsed = time.monotonic() - start

            if i < times - 1:
                time.sleep(max(0, 1 - elapsed))

    except KeyboardInterrupt:
        print("\nStopping!!!")

    finally:
        printStatistics(sent, rtt_cnt, rtt_min, rtt_max, rtt_sum)


ping()
