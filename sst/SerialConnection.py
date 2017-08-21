# -*- coding: utf-8 -*-
"""
@author: lin
"""
from struct import unpack
import serial
from queue import Queue

class SerialConnection(object):
    '''
    Encapsulation for serial connection
    '''
    EVENT_LENGTH = 2
    TIMESTAMP_LENGTH = 4
    START_MARKER = '<'
    END_MARKER = '>'

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.complete_data = Queue()
        self.read_in_process = False
        self.new_data_obtained = False
        self.each_data = bytearray()
        try:
            self.connection = serial.Serial(self.port, self.baudrate)
        except serial.SerialException as e:
            print('Serial Connection Exception {0}'.format(e))

    def isNull(self):
        return self.connection == None

    def opened(self):
        return not self.connection == None

    def write(self, something, append_headers=True):
        if self.opened():
            if append_headers:
                to_send = self.START_MARKER + something +self.END_MARKER
            else:
                to_send = something
            self.connection.write(to_send.encode())

    def read(self):
        if self.opened():
            while self.connection.in_waiting:
                _ = self.connection.read()
                if self.read_in_process:
                    if len(self.each_data) < self.EVENT_LENGTH + self.TIMESTAMP_LENGTH:
                        self.each_data += _
                    elif len(self.each_data) == self.EVENT_LENGTH + self.TIMESTAMP_LENGTH:
                        self.read_in_process = False
                        self.complete_data.put(self._process_each_data(self.each_data))
                        self.each_data = bytearray()
                    else:
                        self.complete_data.put(self._process_each_data(self.each_data[:6]))
                        self.each_data = self.each_data[6:]
                elif _ == self.START_MARKER.encode():
                    self.read_in_process = True
        return self.complete_data

    def _process_each_data(self, data_array):
        if len(data_array) == self.EVENT_LENGTH + self.TIMESTAMP_LENGTH:
            try:
                event = data_array[0:self.EVENT_LENGTH].decode()
            except UnicodeDecodeError:
                event = 'UnicodeError'
            ts = data_array[self.EVENT_LENGTH:]
            try:
                timestamp = unpack('<l', ts)[0]
            except:
                timestamp = ts
        else:
            event = 'DataLengthError'
            timestamp = data_array
        return (event, timestamp)

    def getPort(self):
        return self.port

    def getBaudrate(self):
        return self.baudrate
