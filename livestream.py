# -*- coding: utf-8 -*-
# Getting live video stream from Tobii


import time
import socket
import threading
import signal
import sys


timeout = 1.0
running = True

# GLASSES_IP = "fd93:27e0:59ca:16:76fe:48ff:fe05:1d43" # IPv6 address scope global
GLASSES_IP = "192.168.71.50"  # IPv4 address
PORT = 49152

# Keep-alive message content used to request live data and live video streams
KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"some_GUID1\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"some_other_GUID1\", \"op\": \"start\"}"


# Create UDP socket
def mksock(peer):
    iptype = socket.AF_INET
    if ':' in peer[0]:
        iptype = socket.AF_INET6
    return socket.socket(iptype, socket.SOCK_DGRAM)


# Callback function
def send_keepalive_msg(socket, msg, peer):
    while running:
        socket.sendto(msg, peer)
        time.sleep(timeout)


def signal_handler(signal, frame):
    stop_sending_msg()
    sys.exit(0)


def stop_sending_msg():
    global running
    running = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    peer = (GLASSES_IP, PORT)

    # Create socket which will send a keep alive message for the live data stream
    data_socket = mksock(peer)
    td = threading.Timer(0, send_keepalive_msg, [data_socket, KA_DATA_MSG, peer])
    td.start()

    # Create socket which will send a keep alive message for the live video stream
    video_socket = mksock(peer)
    tv = threading.Timer(0, send_keepalive_msg, [video_socket, KA_VIDEO_MSG, peer])
    tv.start()

    img = []

    while True:
        data, addr = video_socket.recvfrom(2048)
        sys.stdout.write(data)
