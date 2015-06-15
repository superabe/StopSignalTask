# -*- coding: utf-8 -*-
"""
Created on Thu May 21 16:56:24 2015

@author: lin
"""
import serial
import queue

class SerialConnection:
    
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.connection=None
        self.tempQueue=queue.Queue()
        self.inCompleteData=''
        try:
            self.connection = serial.Serial(self.port, self.baudrate)
        except serial.SerialException as e:
            print(e)
        
    def opened(self):
        return not self.connection==None
        
    def write(self, something):
        if(self.opened()):
            self.connection.write(something.encode())
    
    def read(self):
        if(self.opened()):
            while(self.connection.inWaiting()):
                try:
                    inChar = self.connection.read().decode()
                    if inChar=='\n':
                        self.tempQueue.put(self.inCompleteData)
                        self.inCompleteData=''
                    else:
                        self.inCompleteData+=inChar
                except UnicodeDecodeError:
                    pass
            return self.tempQueue
     
    def getPort(self):
        return self.port
        
    def getBaudrate(self):
        return self.baudrate
