# -*- coding: utf-8 -*-

import struct


class MpegTsPacketParser:
    def __init__(self):
        self.PAT_id = 0x0
        self.packet_size = 188

    def parse_packet(self, packet):
        # packet = packet.encode('hex')
        # self.parse_header(packet[:4])
        offset = 0
        while True:
            ts_packet = packet[offset:offset+self.packet_size]
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
                adaptation_field_size = ts_packet[:1]
                ts_packet = ts_packet[adaptation_field_size+1:] # adaptation_field + pointer

            if (adaptation_field_ctrl == 0x1) | (adaptation_field_ctrl == 0x3):
                # adaption_fieldなし

                if pid == 0x00:
                    # PAT
                    pass
                if pid == 0x20:
                    # PMT
                    pass

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
            if pid == 0x40:
                if payload_unit_start_indicator == 1:
                    payload_unit_start_indicator_idx = len(data_lst)
                data_lst.append(ts_packet)

        return payload_unit_start_indicator_idx, data_lst

    def parse_header(self, header):
        packet_header = struct.unpack('>L', header)[0]

        sync_byte = (packet_header >> 24)
        if sync_byte != 0x47:
            print 'Oops! Can NOT found Sync_Byte! maybe something wrong with the file'

        self.payload_unit_start_indicator = (packet_header >> 22) & 0x1
        self.pid = ((packet_header >> 8) & 0x1FFF)


