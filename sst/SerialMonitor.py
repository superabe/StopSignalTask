# -*- coding: utf-8 -*-
"""
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
        self.data=data
        self.connection=conn
        self.alive=True

    def __del__(self):
        self.wait()

    def run(self):
        while self.alive:
            data_in = self.connection.read()
            if data_in:
                for d in data_in:
                    k=self.data.write(d)
                    if k==0:
                        self.state.emit()
    def stop(self):
        self.alive = False

    def get_data(self):
        return self.data
