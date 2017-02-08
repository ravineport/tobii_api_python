# -*- coding: utf-8 -*-

import struct
import cv2
import numpy as np
import socket
import sys

class MpegTsPacketParser:
    def __init__(self):
        self.PAT_id = 0x0
        self.packet_size = 188

    def parse_for_tobii(self, packet):
        payload_unit_start_indicator_idx = -1
        data_lst = []
        packet_size = len(packet) / 188

        for i in range(0, packet_size):
            start = i * self.packet_size
            ts_packet = packet[start:start + self.packet_size]
            packet_header = struct.unpack('>L', ts_packet[:4])[0]
            sync_byte = (packet_header >> 24)
            if sync_byte != 0x47:
                print 'Oops! Can NOT found Sync_Byte! maybe something wrong with the file'

            payload_unit_start_indicator = (packet_header >> 22) & 0x1
            pid = ((packet_header >> 8) & 0x1FFF)
            if pid == 0x00 or pid == 0x20:
                continue
            adaptation_field_ctrl = ((packet_header >> 4) & 0x3)
            adaptation_field_length = 0

            ts_packet = ts_packet[4:]

            if (adaptation_field_ctrl == 0x2) | (adaptation_field_ctrl == 0x3):
                # adaption_fieldをとりあえずカット
                adaptation_field_size = struct.unpack('>B', ts_packet[:1])[0]
                ts_packet = ts_packet[adaptation_field_size+1:]

            if pid == 0x40:
                if payload_unit_start_indicator == 1:
                    # print 'header: 0x%X' % packet_header
                    payload_unit_start_indicator_idx = len(data_lst)
                data_lst.extend(ts_packet)

        return payload_unit_start_indicator_idx, data_lst


if __name__ == "__main__":
    s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_sock.bind(('127.0.0.1', 5002))
    s_sock.listen(10)

    h = 1920
    w = 1080
    size = h * w

    mpeg_ts_parser = MpegTsPacketParser()
    f = open('./mpeg-ts-parser/videos/test2.ts', 'rb')

    img = []

    while True:
        c_sock, addr = s_sock.accept()
        print addr

        while True:
            d = f.read(188 * 10)
            idx, data = mpeg_ts_parser.parse_for_tobii(d)
            if idx == -1 or img == []:
                for d in data:
                    img.extend(d)
            else:
                for d in data[:idx]:
                    img.extend(d)
                img = img[14:]
                # sys.stdout.write(''.join(img))
                c_sock.sendall(''.join(img))
                # img_str = ''.join(img)
                # img_np = np.fromstring(img_str, dtype=np.uint8)
                # print img_np.shape
                # y = img_np[0:size].reshape(h, w)
                # u = img_np[size:(size+(size/4))].reshape((h/2), (w/2))
                # u_upsize = cv2.pyrUp(u)
                # v = img_np[(size + (size / 4)):].reshape((h / 2), (w / 2))
                # v_upsize = cv2.pyrUp(v)
                # yuv = cv2.merge((y, u_upsize, v_upsize))
                # rgb = cv2.cvtColor(yuv, cv2.cv.CV_YCrCb2RGB)
                # cv2.imshow("show", rgb)

                img = data[idx:]
