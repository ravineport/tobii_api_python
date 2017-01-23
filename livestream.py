# -*- coding: utf-8 -*-

import time
import socket
import threading
import signal
import sys
import cv2
import numpy as np

timeout = 1.0
running = True

# GLASSES_IP = "fd93:27e0:59ca:16:76fe:48ff:fe05:1d43" # IPv6 address scope global
GLASSES_IP = "192.168.71.50"  # IPv4 address
PORT = 49152

# Keep-alive message content used to request live data and live video streams
KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"some_GUID\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"some_other_GUID\", \"op\": \"start\"}"

# Gstreamer pipeline definition used to decode and display the live video stream
PIPELINE_DEF = "udpsrc do-timestamp=true name=src blocksize=1316 closefd=false buffer-size=5600 !" \
               "mpegtsdemux !" \
               "queue !" \
               "ffdec_h264 max-threads=0 !" \
               "ffmpegcolorspace !" \
               "xvimagesink name=video"


# Create UDP socket
def mksock(peer):
    iptype = socket.AF_INET
    if ':' in peer[0]:
        iptype = socket.AF_INET6
    return socket.socket(iptype, socket.SOCK_DGRAM)


# Callback function
def send_keepalive_msg(socket, msg, peer):
    while running:
        print("Sending " + msg + " to target " + peer[0] + " socket no: " + str(socket.fileno()) + "\n")
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

    while True:
        data, addr = video_socket.recvfrom(1024)
        cv2.imshow('test', data)
        # print "received message:", data
        # bytes = ''
        # try:
        #     bytes += data
        #     a = bytes.find('\xff\xd8')
        #     b = bytes.find('\xff\xd9')
        #     if a != -1 and b != -1:
        #         jpg = bytes[a:b + 2]
        #         bytes = bytes[b + 2:]
        #         img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
        #         cv2.imshow('cam', img)
        #         if cv2.waitKey(1) == 27:
        #             exit(0)
        # except threading.ThreadError:
        #     stop_sending_msg()


    # Create gstreamer pipeline and connect live video socket to it
    # pipeline = None
    # try:
    #     pipeline = gst.parse_launch(PIPELINE_DEF)
    # except Exception, e:
    #     print e
    #     stop_sending_msg()
    #     sys.exit(0)
    #
    # src = pipeline.get_by_name("src")
    # src.set_property("sockfd", video_socket.fileno())
    #
    # pipeline.set_state(gst.STATE_PLAYING)
    #
    # while running:
    #     # Read live data
    #     data, address = data_socket.recvfrom(1024)
    #     print (data)
    #
    #     state_change_return, state, pending_state = pipeline.get_state(0)
    #
    #     if gst.STATE_CHANGE_FAILURE == state_change_return:
    #         stop_sending_msg()