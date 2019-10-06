#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time

GET_NOW_POWER_CMD = b'\x10\x81\x12\x34\x05\xFF\x01\x02\x88\x01\x62\x01\xE7\x01\x01'
GET_EACH30_CMD =   b'\x10\x81\x12\x34\x05\xFF\x01\x02\x88\x01\x62\x01\xE2\x00'
GET_NOW_POWER_B_CMD = b'\x10\x81\x12\x34\x05\xFF\x01\x02\x88\x01\x62\x01\xE7\x01\x01'
GET_EACH30_B_CMD =    b'\x10\x81\x12\x34\x05\xFF\x01\x02\x88\x01\x62\x01\xE2\x00\x03'
GET_STATUS_B_CMD =   b'\x10\x81\x12\x34\x05\xFF\x01\x02\x88\x01\x62\x01\x88'
GET_MF_B_CMD =   b'\x10\x81\x12\x34\x05\xFF\x01\x02\x88\x01\x62\x01\xE1'

class WiSUNClient(object):
    RE
    def __init__(self, serial_port, baudrate=115200, timeout=1):
        self.ser = serial.Serial()
        self.ser.port = serial_port
        self.ser.baudrate = baudrate
        self.open()

    def open(self):
        if not self.ser.is_open:
            self.ser.open()

    def close(self):
        if self.ser.is_open:
            self.ser.close() 
   
    def set_credential(self, id, password):
        self.command('SKSETRBID %s' % id)
        self.command('SKSETPWD C %s' % password)

    def scan(self, timeout=6):
        device = {}
        self._write('SKSCAN 2 FFFFFFFF %d' % timeout)
        self._read(False) # for echo back
        time.sleep(timeout)
        is_found = False
        is_scan_end = False
        while not is_scan_end:
            line = self._read()
            if line.startswith('EVENT 22'):
                is_scan_end = True
                continue
            if line.startswith('EVENT 20'):
                is_found = True
                continue
            if is_found:
                if line == 'EPANDESC':
                    continue
                split = line.strip().split(':')
                if split[0] == 'Channel':
                    device['Channel'] = split[1]
                if split[0] == 'Channel Page':
                    device['Channel Page'] = split[1]
                if split[0] == 'Pen ID':
                    device['Pen ID'] = split[1]
                if split[0] == 'Addr':
                    device['Addr'] = split[1]
                if split[0] == 'LQI':
                    device['LQI'] = split[1]
                if split[0] == 'PairID':
                    device['PairID'] = split[1]
        return device
        
    def set_channel(self, channel):
        self.command('SKSREG S2 %s' & channel)

    def set_penid(self, penid):
        self.command('SKSREG S3 %s' % penid)

    def mac2ipv6(self, mac):
        return self.command('SKLL64 %s' % mac).strip()

    def connect(self, ipv6):
        self._write('SKJOIN %s' % ipv6)
        is_connected = False
        while not is_connected:
            line = self._read()
            if line.startswith('EVENT 24'):
                raise Exception('connection failed: %s' % ipv6)
            if line.startswith('EVENT 25'):
                is_connected = True

    def get_power(self, ipv6):
        cmd = 'SKSENDTO 1 %s 0E1A 1 %04x %s' % (ipv6, len(GET_NOW_POWER_CMD), GET_NOW_POWER_CMD)
        self.command(cmd)
        is_get_power = False
        while not is_get_power:
            line = self._read()
            if line.startswith('ERXUDP'):
                split = line.strip().split(' ')
                res = split[8]
                tid = res[4:4+4]
                seoj = res[8:8+6]
                deoj = res[14,14+6]
                ESV = res[20:20+2]
                OPC = res[22,22+2]
                if seoj == '028801' and ESV == '72' :
                    EPC = res[24:24+2]
                    if EPC == 'E0':
                        pwMul = int(res[40:42], 16)
                        pwTotal = round(int(res[28:36], 16) * self.multi(pwMul), 1)
                        pw = int(res[46:54], 16)
                        print(u'計測値:{0}[W], {1}[kW], {2}'.format(pw, pwTotal, pwMul))
                        self.store.store(datetime.datetime.now(), pw, pwTotal)

    def command(self, cmd):
        self._write(cmd)
        self._read(False) # for echo back
        status = self._read()
        if not status.startswith('OK'):
            raise Exception('status is %s' % status)
        result = ''
        while self.ser.in_waiting > 0:
            time.sleep(0.1)
            result += self._read()
        return result

    # Private Method
    def _generate_cmd(self, cmd):

    def _write(self, cmd, is_print=True):
        if is_print:
            print('>> %s' % cmd)
        self.ser.write(('%s\r\n' % cmd).encode())

    def _read(self, is_print=True):
        time.sleep(0.1)
        data = self.ser.readline().decode()
        if is_print:
            print('<< %s' % data)
        return data
