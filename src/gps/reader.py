# Source: https://pypi.org/project/pynmea2/1.8.0/
# !/usr/bin/python
# -*- coding:utf-8 -*-

import pynmea2
import configparser
import RPi.GPIO as GPIO
import serial
import time


from math import radians, cos, sin, asin, sqrt
from settings import CONFIG_FILE, GPS_POWER_KEY


class GPSReader:
    def __init__(self):
        params = configparser.ConfigParser()
        params.read(CONFIG_FILE)
        self.rec_buff = ''
        self.serial_port = serial.Serial(params.get("GPS", "port"), baudrate=115200)
        self.serial_port.flushInput()
        self.__initialize()

    def __initialize(self):
        # power on
        print('[INFO] SIM7600X is starting:')
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(GPS_POWER_KEY, GPIO.OUT)
        time.sleep(0.1)
        GPIO.output(GPS_POWER_KEY, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(GPS_POWER_KEY, GPIO.LOW)
        time.sleep(20)
        self.serial_port.flushInput()
        print('[INFO] SIM7600X is ready')

    def send_at(self, command, back, timeout):
        self.rec_buff = ''
        self.serial_port.write((command + '\r\n').encode())
        time.sleep(timeout)
        if self.serial_port.inWaiting():
            time.sleep(0.01)
            self.rec_buff = self.serial_port.read(self.serial_port.inWaiting())
        if self.rec_buff != '':
            if back not in self.rec_buff.decode():
                print(f"[INFO] {command} ERROR")
                print(f"[INFO] {command} back:\t {self.rec_buff.decode()}")
                return None
            else:
                gps_info = self.rec_buff.decode()
                print(f"[INFO] Success: {gps_info}")
                gps_info = gps_info[gps_info.find(":") + 1:]
                lat = gps_info.split(",")[0]
                lon = gps_info.split(",")[2]
                return lat, lon
        else:
            print('[INFO] GPS is not ready')
            return None

    def get_gps_position(self):
        lat = ""
        lon = ""
        rec_null = True
        print('Start GPS session...')
        self.rec_buff = ''
        self.send_at('AT+CGPS=1,1', 'OK', 1)
        time.sleep(2)
        while rec_null:
            answer = self.send_at('AT+CGPSINFO', '+CGPSINFO: ', 1)
            if answer is not None:
                lat, lon = answer
                rec_null = False
            time.sleep(1.5)

        return lat, lon

    @staticmethod
    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula
        d_lon = lon2 - lon1
        d_lat = lat2 - lat1
        a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers. Use 3956 for miles

        return c * r

    def extract_lat_lon(self):
        while True:
            f_nmea_msg = self.serial_port.readline().decode().replace("\r\n", "")
            print(f"[INFO] First Nmea MSG: {f_nmea_msg}")
            if f_nmea_msg.find('GGA') > 0:
                break
        f_msg = pynmea2.parse(f_nmea_msg)
        lat = f_msg.lat
        lon = f_msg.lon
        print(f"[INFO] Latitude: {lat}")
        print(f"[INFO] Longitude: {lon}")
        while True:
            s_nmea_msg = self.serial_port.readline().decode().replace("\r\n", "")
            print(f"[INFO] Second Nmea MSG: {s_nmea_msg}")
            if s_nmea_msg.find('GGA') > 0:
                break
        s_msg = pynmea2.parse(s_nmea_msg)
        gps_speed = self.haversine(float(lat), float(lon), float(s_msg.lat), float(s_msg.lon))
        print(F"[INFO] GPS speed: {gps_speed}km/hr")

        return lat, lon, gps_speed


if __name__ == '__main__':
    GPSReader().extract_lat_lon()
