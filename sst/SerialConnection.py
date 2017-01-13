# -*- coding: utf-8 -*-
"""
@author: lin
"""
from struct import unpack
import serial

class SerialConnection(object):
    '''
    Encapsulation for serial connection
    '''
    EVENT_LENGTH = 2
    TIMESTAMP_LENGTH = 4

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.complete_data = None
        try:
            self.connection = serial.Serial(self.port, self.baudrate)
        except serial.SerialException as e:
            print('Serial Connection Exception {0}'.format(e))

    def isNull(self):
        return self.connection == None

    def opened(self):
        return not self.connection == None

    def write(self, something):
        if self.opened():
            self.connection.write(something.encode())

    def read(self):
        if self.opened():
            self.complete_data = []
            while self.connection.in_waiting:
                try:
                    _ = self.connection.read().decode()
                    if _ == '<':
                        event = self.connection.read(self.EVENT_LENGTH).decode()
                        ts = self.connection.read(self.TIMESTAMP_LENGTH)
                        try:
                            timestamp = unpack('<l', ts)[0]
                        except:
                            timestamp = -1
                        self.complete_data.append((event, timestamp))
                except UnicodeDecodeError:
                    event = 'Error'
                    self.complete_data.append((event, timestamp))
        return self.complete_data

    def getPort(self):
        return self.port

    def getBaudrate(self):
        return self.baudrate
