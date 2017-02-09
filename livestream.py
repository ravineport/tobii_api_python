# -*- coding: utf-8 -*-

import time
import socket
import threading
import signal
import sys
import struct
import cv2
import numpy as np


class MpegTsPacketParser:
    def __init__(self):
        self.PAT_id = 0x0
        self.packet_size = 188

    def parse_for_tobii(self, packet):
        offset = 0
        payload_unit_start_indicator_idx = -1
        data_lst = []
        packet_size = len(packet) / 188

        for i in range(0, packet_size):
            ts_packet = packet[offset:offset + self.packet_size]
            packet_header = struct.unpack('>L', ts_packet[:4])[0]
            ts_packet = ts_packet[4:]
            sync_byte = (packet_header >> 24)
            if sync_byte != 0x47:
                print 'Oops! Can NOT found Sync_Byte! maybe something wrong with the file'

            payload_unit_start_indicator = (packet_header >> 22) & 0x1
            pid = ((packet_header >> 8) & 0x1FFF)
            adaptation_field_ctrl = ((packet_header >> 4) & 0x3)
            adaptation_field_length = 0

            if (adaptation_field_ctrl == 0x2) | (adaptation_field_ctrl == 0x3):
                # adaption_fieldをとりあえずカット
                adaptation_field_size = struct.unpack('>B', ts_packet[:1])[0]
                ts_packet = ts_packet[adaptation_field_size+1:]

            if pid == 0x40:
                if payload_unit_start_indicator == 1:
                    payload_unit_start_indicator_idx = len(data_lst)
                data_lst.append(ts_packet)

        return payload_unit_start_indicator_idx, data_lst

timeout = 1.0
running = True

# GLASSES_IP = "fd93:27e0:59ca:16:76fe:48ff:fe05:1d43" # IPv6 address scope global
GLASSES_IP = "192.168.71.50"  # IPv4 address
PORT = 49152

# Keep-alive message content used to request live data and live video streams
KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"some_GUID1\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"some_other_GUID1\", \"op\": \"start\"}"

# Gstreamer pipeline definition used to decode and display the live video stream
# PIPELINE_DEF = "udpsrc do-timestamp=true name=src blocksize=1316 closefd=false buffer-size=5600 !" \
#                "mpegtsdemux !" \
#                "queue !" \
#                "ffdec_h264 max-threads=0 !" \
#                "ffmpegcolorspace !" \
#                "xvimagesink name=video"


# Create UDP socket
def mksock(peer):
    iptype = socket.AF_INET
    if ':' in peer[0]:
        iptype = socket.AF_INET6
    return socket.socket(iptype, socket.SOCK_DGRAM)


# Callback function
def send_keepalive_msg(socket, msg, peer):
    while running:
        # print("Sending " + msg + " to target " + peer[0] + " socket no: " + str(socket.fileno()) + "\n")
        socket.sendto(msg, peer)
        time.sleep(timeout)


def signal_handler(signal, frame):
    stop_sending_msg()
    sys.exit(0)


def stop_sending_msg():
    global running
    running = False


if __name__ == "__main__":
    mpeg_ts_parser = MpegTsPacketParser()
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
        # idx, data = mpeg_ts_parser.parse_for_tobii(data)
        sys.stdout.write(data)
        # if idx == -1:
        #     for d in data:
        #         img.extend(d)
        # else:
        #     for d in data[:idx]:
        #         img.extend(d)
        #     print(np.array(img).shape)
        #     cv2.imshow('test', np.array(img))
        #     img = []
        # cv2.imshow('test', data)
        # sys.stdout.write(data)
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
