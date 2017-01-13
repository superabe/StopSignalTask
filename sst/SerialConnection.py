# -*- coding: utf-8 -*-
"""
@author: lin
"""
import serial
from struct import unpack

class SerialConnection:

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.connection=None
        self.completeData=None
        try:
            self.connection = serial.Serial(self.port, self.baudrate, timeout=3)
        except serial.SerialException as e:
            print(e)

    def isNull(self):
        return self.connection == None

    def opened(self):
        return not self.connection==None

    def write(self, something):
        if(self.opened()):
            self.connection.write(something.encode())

    def read(self):
        if(self.opened()):
            self.completeData=[]
            while(self.connection.in_waiting):
                try:
                    data_in = self.connection.read().decode()
                    if data_in == '<':
                        counter = 0
                        event = ''
                        ts = b''
                        while True:
                            if counter == 2:
                                counter = 0
                                break
                            event += self.connection.read().decode()
                            counter += 1
                        while True:
                            if counter == 4:
                                counter = 0
                                break
                            ts += self.connection.read()
                            counter += 1
                        try:
                            timestamp = unpack('<l',ts)[0]
                        except:
                            timestamp = 0
                        self.completeData.append(event+','+str(timestamp))
                except UnicodeDecodeError:
                    pass
        return self.completeData

    def getPort(self):
        return self.port

    def getBaudrate(self):
        return self.baudrate
