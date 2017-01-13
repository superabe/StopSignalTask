# -*- coding: utf-8 -*-
"""
Modified from https://github.com/eliben/code-for-blog/tree/master/2009/plotting_data_monitor
"""

from PyQt5.QtCore import QThread, pyqtSignal


class SerialMonitor(QThread):
    """ A thread for monitoring a serial port. The serial port is
        opened when the thread is started.
    """
    STATE = pyqtSignal()

    def __init__(self, data, conn):
        QThread.__init__(self)
        self.data = data
        self.connection = conn
        self.alive = True

    def __del__(self):
        self.wait()

    def run(self):
        '''
        workload of the thread
        '''
        while self.alive:
            data_in = self.connection.read()
            if data_in:
                for each_data in data_in:
                    k = self.data.write(each_data)
                    if k == 0:
                        self.STATE.emit()
    def stop(self):
        '''
        stop the thread
        '''
        self.alive = False

    def get_data(self):
        '''
        return the data
        '''
        return self.data
