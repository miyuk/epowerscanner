#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import yaml
import wisun
import influxdb

# 設定読み込み
print('### 設定読み込み ###')
config = yaml.safe_load(open('config.yml', 'r'))
# Bルート認証ID（東京電力パワーグリッドから郵送で送られてくるヤツ）
BROOT_ID = config['BROOT_ID']
# Bルート認証パスワード（東京電力パワーグリッドからメールで送られてくるヤツ）
BROOT_PASSWORD = config['BROOT_PASSWORD']
SERIAL_PORT = config['SERIAL_PORT']
DB_HOST = config['DB_HOST']
DB_PORT = config['DB_PORT']
DB_DBNAME = config['DB_DBNAME']
DB_MEASUREMENT = config['DB_MEASUREMENT']
DB_USERNAME = config['DB_USERNAME']

DB_PASSWORD = config['DB_PASSWORD']

def main():
    try:
        print('### Serial設定 ###')
        client = wisun.WiSUNClient(SERIAL_PORT)
        print('### Mode設定 ###')
        client.set_option('01')
        print('### 認証情報設定 ###')
        client.set_credential(BROOT_ID, BROOT_PASSWORD)
        print('### スキャン開始 ###')
        for x in range(5):
            device = client.scan()
            if device:
                ipv6 = client.mac2ipv6(device['Addr'])
                break
        print('### 各種パラメータ設定 ###')
        client.set_channel(device['Channel'])
        client.set_panid(device['Pan ID'])
        print('### デバイス接続 ###')
        client.connect(ipv6)
        print('### 瞬時値、積算値取得 ###')
        instanted = client.fetch_instaneous_power(ipv6)
        integrated = client.fetch_integrated_power(ipv6)
        unit = client.fetch_integrated_power_unit(ipv6)
        send_data(instanted, integrated * unit)
    except:
        raise
    finally:
        print('### 切断 ###')
        client.close()

def send_data(instanted, integrated):
    client = influxdb.InfluxDBClient(host=DB_HOST,
                                     port=DB_PORT,
                                     database=DB_DBNAME,
                                     username=DB_USERNAME,
                                     password=DB_PASSWORD)
    data = [
        {
            'measurement': DB_MEASUREMENT,
            'tags': {
                'location': 'tokyo'
            },
            'fields': {
                'instantneous': instanted,
               'integrated': integrated
             }
        }
    ]
    if client.write_points(data):
        print('measurement is successed')
    client.close()

if __name__ == '__main__':
    main()

