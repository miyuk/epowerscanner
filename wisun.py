#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time

GET_NOW_POWER_CMD = b'\x10\x81\x12\x34\x05\xFF\x01\x02\x88\x01\x62\x01\xE7\x01\x01'

def gen_smartmater_cmd(cmd):
    fmt = '10 81 00 01 05 ff 01 02 88 01 62 01 %s 00'.replace(' ', '')
    return bytes.fromhex(fmt % cmd)

class WiSUNClient(object):
    def __init__(self, serial_port, baudrate=115200, timeout=10):
        self.ser = serial.Serial()
        self.ser.port = serial_port
        self.ser.baudrate = baudrate
        self.ser.timeout = timeout
        self.open()

    def open(self):
        if not self.ser.is_open:
            self.ser.open()
            self._write('SKRESET')
            while True:
               if self._read() == 'OK':
                   break
            self._write('SKSREG SFE 0')
            self._read()
            self._read()

    def close(self):
        if self.ser.is_open:
            self.ser.close() 
   
    def set_option(self, mode):
        status, result = self.command('ROPT', with_status=True, end_of_line='\r')
        if status.split(' ')[1] == mode:
            print('option(%s) is already configured' % mode)
            return
        self.command('WOPT %s' % mode, end_of_line='\r')

    def set_credential(self, id, password):
        self.command('SKSETRBID %s' % id)
        self.command('SKSETPWD C %s' % password)

    def scan(self, timeout=6):
        device = {}
        self._write('SKSCAN 2 FFFFFFFF %d' % timeout)
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
                if split[0] == 'Pan ID':
                    device['Pan ID'] = split[1]
                if split[0] == 'Addr':
                    device['Addr'] = split[1]
                if split[0] == 'LQI':
                    device['LQI'] = split[1]
                if split[0] == 'PairID':
                    device['PairID'] = split[1]
        return device
        
    def set_channel(self, channel):
        self.command('SKSREG S2 %s' % channel)

    def set_panid(self, panid):
        self.command('SKSREG S3 %s' % panid)

    def mac2ipv6(self, mac):
        status, result = self.command(('SKLL64 %s' % mac), with_status=False)
        return result.strip()

    def connect(self, ipv6):
        self._write('SKJOIN %s' % ipv6)
        is_connected = False
        while not is_connected:
            line = self._read()
            if line.startswith('EVENT 24'):
                raise Exception('connection failed: %s' % ipv6)
            if line.startswith('EVENT 25'):
                is_connected = True

    def fetch_instaneous_power(self, ipv6, timeout=6):
        now_cmd = gen_smartmater_cmd('E7')
        cmd = b'SKSENDTO 1 %s 0E1A 1 %04x ' % (ipv6.encode(), len(now_cmd))
        cmd = cmd + now_cmd
        self._write(cmd)
        while True:
            line = self._read()
            if line.startswith('OK'):
                continue
            if line.startswith('EVENT 21'):
                continue
            if line.startswith('ERXUDP'):
                split = line.split(' ')
                ebc = int(split[7], 16)
                res = bytes.fromhex(split[8])
                seoj = res[4:4+3]
                deoj = res[7:7+3]
                esv = res[10:10+1]
                if seoj == bytes.fromhex('028801') and esv == bytes.fromhex('72'):
                    epc = res[12:12+1]
                    if epc == bytes.fromhex('E7'):
                        power = int.from_bytes(res[-4:], 'big')
                        return power

    def fetch_integrated_power(self, ipv6, timeout=6):
        now_cmd = gen_smartmater_cmd('E0')
        cmd = b'SKSENDTO 1 %s 0E1A 1 %04x ' % (ipv6.encode(), len(now_cmd))
        cmd = cmd + now_cmd
        self._write(cmd)
        while True:
            line = self._read()
            if line.startswith('OK'):
                continue
            if line.startswith('EVENT 21'):
                continue
            if line.startswith('ERXUDP'):
                split = line.split(' ')
                ebc = int(split[7], 16)
                res = bytes.fromhex(split[8])
                seoj = res[4:4+3]
                deoj = res[7:7+3]
                esv = res[10:10+1]
                if seoj == bytes.fromhex('028801') and esv == bytes.fromhex('72'):
                    epc = res[12:12+1]
                    if epc == bytes.fromhex('E0'):
                        power = int.from_bytes(res[-4:], 'big')
                        return power

    def fetch_integrated_power_unit(self, ipv6, timeout=6):
        now_cmd = gen_smartmater_cmd('E1')
        cmd = b'SKSENDTO 1 %s 0E1A 1 %04x ' % (ipv6.encode(), len(now_cmd))
        cmd = cmd + now_cmd
        self._write(cmd)
        while True:
            line = self._read()
            if line.startswith('OK'):
                continue
            if line.startswith('EVENT 21'):
                continue
            if line.startswith('ERXUDP'):
                split = line.split(' ')
                ebc = int(split[7], 16)
                res = bytes.fromhex(split[8])
                seoj = res[4:4+3]
                deoj = res[7:7+3]
                esv = res[10:10+1]
                if seoj == bytes.fromhex('028801') and esv == bytes.fromhex('72'):
                    epc = res[12:12+1]
                    if epc == bytes.fromhex('E1'):
                        unit_char = res[-1:]
                        if unit_char == b'\x00':
                            return 1.0
                        elif unit_char == b'\x01':
                            return 0.1
                        elif unit_char == b'\x02':
                            return 0.01
                        elif unit_char == b'\x03':
                            return 0.001
                        elif unit_char == b'\x04':
                            return 0.0001
                        elif unit_char == b'\x0A':
                            return 10.0
                        elif unit_char == b'\x0B':
                            return 100.0
                        elif unit_char == b'\x0C':
                            return 1000.0
                        elif unit_char == b'\x0D':
                            return 10000.0
                        

    def command(self, cmd, with_status=True, with_echoback=False, as_ascii=True, end_of_line='\r\n', timeout=0.1):
        status = None
        self._write(cmd)
        if with_echoback:
            self._read(False) # ignore echoback
        if with_status:
            status = self._read(as_ascii=as_ascii, end_of_line=end_of_line)
            if not status.startswith('OK'):
                raise Exception('status is %s' % status)
        time.sleep(timeout)
        result = ''
        while self.ser.in_waiting > 0:
            result += self._read(as_ascii=as_ascii, end_of_line=end_of_line)
        return (status, result)

    # Private Method
    def _generate_cmd(self, cmd):
        pass

    def _write(self, cmd, is_print=True):
        if type(cmd) is str:
            send_cmd = ('%s\r\n' % cmd).encode()
        elif type(cmd) is bytes:
            send_cmd = (b'%s\r\n' % cmd)
        if is_print:
            print('<< %s' % cmd)
        self.ser.write(send_cmd)

    def _read(self, is_print=True, as_ascii=True, end_of_line='\r\n', timeout=10):
        end_of_line = end_of_line.encode()
        time.sleep(0.1)
        data = b''
        while True:
            data += self.ser.read()
            if data.endswith(end_of_line):
                break
        if as_ascii:
            data = data.decode().strip(end_of_line.decode())
        else:
            data = data.strip(end_of_line)
        if is_print:
            if as_ascii:
                print('>> %s' % data.strip(end_of_line.decode()))
            else:
                print('>> %s' % data.strip(end_of_line))
        return data
