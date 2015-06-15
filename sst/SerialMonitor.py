# -*- coding: utf-8 -*-
"""
Created on Fri May 15 17:35:45 2015

Modified from https://github.com/eliben/code-for-blog/tree/master/2009/plotting_data_monitor
"""

from PyQt5.QtCore import QThread,pyqtSignal


class SerialMonitor(QThread):
    """ A thread for monitoring a serial port. The serial port is 
        opened when the thread is started.
    """
    state = pyqtSignal()
    
    def __init__(self, data, conn):
        QThread.__init__(self)
        self.data = data
        self.connection=conn
        self.stopped=False
            
    def __del__(self):
        self.wait()        
    
        
    def run(self):       
        while not self.stopped:
            incomingData = self.connection.read()
            while(not incomingData.empty()):
                data = incomingData.get()
                incomingData.task_done()
                k=self.data.write(data)
                if k==0:
                    self.state.emit()
    
    def stop(self):
        self.stopped = True
    
    def getData(self):
        return self.data
