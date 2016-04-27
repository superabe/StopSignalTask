'''
This is the main gui module
'''
import sys
import os
import time
import random
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QSizePolicy,QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap,QValidator, QIntValidator

import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from .sst_summary import calCR, calRT, median, calSSRT2
from .sst_mainwindow import Ui_MainWindow
from .sst_newTraining import Ui_Dialog
from .SerialConnection import SerialConnection
from .SerialMonitor import SerialMonitor
from .Data import Data


class mainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, port='com3', baudrate=115200):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.parameters={}
        self.configured=False
        self.sessionStartTime=0
        self.trialNum=0
        self.timeSinceStart=0
        self.isRunning=False
        self.histPlot = MyHistCanvas()
        self.rtDisplay.addWidget(self.histPlot)
        self.resultSaved = True
        self.port = port
        self.baudrate=baudrate
        self.connection = SerialConnection(self.port, self.baudrate)        
        self.serialMonitor=None
        self.testReward_button.setEnabled(False)
        self.testStopSignal_button.setEnabled(False)
        # new training setting window
        self.newTraining=NewTraining()
        
        # timers
        self.timerForTimeDisplay=QTimer()
        self.timerForRuningDisplay=QTimer()

        
        # connect signals to slots

        self.actionNew_Training.triggered.connect(self.openNewTraining)
        self.start_button.released.connect(self.sessionStart)
        self.end_button.released.connect(self.sessionEnd)
        self.testReward_button.pressed.connect(self.testRewardStart)
        self.testReward_button.released.connect(self.testRewardEnd)
        self.testStopSignal_button.pressed.connect(self.testStopSignal)
        self.testLaser_button.pressed.connect(self.testLaserOn)
        self.testLaser_button.released.connect(self.testLaserOff)
        self.timerForTimeDisplay.timeout.connect(self.timeElapsedLabelUpdate)
        self.timerForRuningDisplay.timeout.connect(self.runingUpdate)
        self.actionAbout.triggered.connect(self.about)

        # initialize display
        self.timeElapsedLabel.setText('0 m 0 s')
    
    def setParams(self, params):
        self.parameters=params
    def getParams(self):
        return self.parameters
		
    def openNewTraining(self):
        if(self.newTraining.exec_()):
            self.setParams(self.newTraining.getParameters())
            self.configured=True
            self.start_button.setEnabled(True)
                

    def sessionStart(self):
        self.isRunning=True
        self.start_button.setEnabled(False)
        self.end_button.setEnabled(True)
        self.actionNew_Training.setEnabled(False)
        if self.resultSaved:
            self.resultSaved=False

        self.sessionStartTime=time.clock()

        self.trialNumLabel.setText('0')
        self.runingLabel.setPixmap(QPixmap(':/on.png'))#.scaled(self.runingLabel.size()))

        self.timerForTimeDisplay.start(1000)
        self.timerForRuningDisplay.start(500)

        # start serial monitor        
        if self.serialMonitor is None:
            self.serialMonitor = SerialMonitor(Data(), self.connection)
        self.serialMonitor.state.connect(self.trialEndUpdate)
        self.serialMonitor.start()
        
        # send session parameters to arduino
        self.sendParams()
        
        # initialize mainwindow display
        self.trialNumLabel.setText('0') 
        self.timeElapsedLabel.setText('0'+' m '+'0'+' s')
        self.goPerfLabel.setText('0%')
        self.stopPerfLabel.setText('0%')
        self.ssrtLabel.setText('0 ms')
        # reset the histogram in rtDisplay
        self.histPlot.reset()

        params = self.getParams()
        if params['direction']=='l':
            textDirection = 'R>L>M'
        else:
            textDirection = 'L>R>M'
        descriptionalText = 'stage: '+str(params['stage'])+'\n'\
                            +'direction: '+textDirection+'\n'
        self.descriptionalLabel.setText(descriptionalText)
        if(params['stage']==6):
                self.testReward_button.setEnabled(True)
                self.testStopSignal_button.setEnabled(True)
                self.testLaser_button.setEnabled(True)
        
    def sendParams(self):
        # send parameters to arduino control program through serial communication
        params=self.getParams()
        if params['stage']==5:
            stopNum=int((int(params['blockLength'])*float(params['stopPercent']))*int(params['blockNumber']))
        else:
            stopNum=int((int(params['sessionLength'])-int(params['baseline']))*float(params['stopPercent']))
        if stopNum>100:
            stopNum=100 # stop number should be less than 100.

        while stopNum%params['blockNumber']!=0: # stop number should be equally distributed in each block.
            params['blockNumber'] -= 1

        paramsToSend = str(params['stage'])+','+params['direction']+','+params['lh']+','\
                           +params['sessionLength']+','+params['baseline']+','+str(stopNum)+','\
                           +params['punishment']+','+params['blockLength']+','+params['blockNumber']+','\
                           +params['reward']+','+params['blinkerFreq']+','+params['isLaser']+','\
                           +params['laserFreq']+','+params['pulseDur']+','+params['laserDur']+','+'\n'
        self.connection.write(paramsToSend)
        return params
            
        
    def timeElapsedLabelUpdate(self):
        self.timeSinceStart+=1
        mins = int(self.timeSinceStart/60)
        secs = int(self.timeSinceStart-60*mins)
        self.timeElapsedLabel.setText(str(mins)+' m '+str(secs)+' s')

    def runingUpdate(self):
        if(self.runingLabel.isVisible()):
            self.runingLabel.setVisible(False)
        else:
            self.runingLabel.setVisible(True)
 
    def trialEndUpdate(self):
        data = self.serialMonitor.getData().getData()
        trialNum = len(data['pokeInM'])
        stage = self.getParams()['stage']    
        
        self.trialNumLabel.setText(str(trialNum))
        if stage>2:
            if self.getParams()['direction']=='l':
                rt = calRT(data['pokeOutR'],data['pokeInL'])
            else:
                rt = calRT(data['pokeOutL'],data['pokeInR'])
            # cal initial ssd and send to control program
            if trialNum==int(self.getParams()['baseline']) and stage==5:
                if median(rt)>200:
                    self.connection.write(str(median(rt)-200)+',')
                else:# If median of rt was less than 200, then stop delay will be set to zero
                    self.connection.write('0,')
            
            cr = calCR(data['trialType'],data['isRewarded'])
            self.goPerfLabel.setText(str(cr['GoTrial']*100)+'%')    
            self.stopPerfLabel.setText(str(cr['StopTrial']*100)+'%')
            if len(rt)>0:
                self.histPlot.update_figure(rt)

    def sessionEnd(self):
        # restart arduino
        self.connection.write('r')
        
        # reset GUI
        self.isRunning=False
        self.end_button.setEnabled(False)        
        self.actionNew_Training.setEnabled(True)
        self.testReward_button.setEnabled(False)
        self.testStopSignal_button.setEnabled(False)
        self.testLaser_button.setEnabled(False)
        self.timerForTimeDisplay.stop()
        self.timerForRuningDisplay.stop()
        self.runingLabel.setVisible(True)
        self.runingLabel.setPixmap(QPixmap('off.png'))#.scaled(self.runingLabel.size()))
        self.timeSinceStart=0
        
        # save data to txt file
        self.saveData()
        self.resultSaved=True        
        
        # close serial monitor
        if self.serialMonitor is not None:
            self.serialMonitor.stop()
            self.serialMonitor=None        
        
        print('Session End')
   
    def closeEvent(self, event):
        if not self.resultSaved:
            result = QMessageBox.question(self, "Exit", 
                                          "Want to exit ? Session In Process!!!",
                                          QMessageBox.Yes|QMessageBox.No)
            event.ignore()
            if result == QMessageBox.Yes:
                self.sessionEnd()
                event.accept()
    
    def saveData(self):
        '''
        Save the result to file
        '''
        ####Create a TXT file to store the result data
        ####Check whether there is a file with the same name as we created first.
    
        now = datetime.datetime.now()
        createdTime = now.strftime("%Y-%m-%d %H-%M")
        fileName = 'SST Report ' + createdTime + '.txt'
        while os.path.exists(fileName):
            fileName = fileName[0:-4] + ' new' + '.txt'
        data = self.serialMonitor.getData().getData()
        f = open(fileName,'w')
        f.write('General Message:\n')
        f.write('trialNum: ')   #### line 2
        f.write(str(len(data['pokeInM']))+' ')
        f.write(str(self.sendParams()))
        f.write('\nPokeInL\n')
        f.write(str(data['pokeInL']))   ####line 4
        f.write('\nPokeOutL\n')
        f.write(str(data['pokeOutL']))   ### 6
        f.write('\nPokeInM\n')
        f.write(str(data['pokeInM']))   ####line 8
        f.write('\nPokeOutM\n')
        f.write(str(data['pokeOutM']))   ### 10
        f.write('\nPokeInR\n')
        f.write(str(data['pokeInR']))   ####line 12
        f.write('\nPokeOutR\n')
        f.write(str(data['pokeOutR']))   ### 14
        f.write('\nRewardStart\n')
        f.write(str(data['rewardStart']))  ### 16
        f.write('\nStopSignalStart\n')
        f.write(str(data['stopSignalStart']))
        f.write('\nTrialType\n')
        f.write(str(data['trialType']))
        f.write('\nIsRewarded\n')
        f.write(str(data['isRewarded']))        
        f.write('\nSSDs\n')
        f.write(str(data['SSDs']))
        f.write('\nTrials Skipped\n')
        f.write(str(data['trialsSkipped']))
        f.write('\nMissed Data\n')
        f.write(str(data['missedData']))
        f.write('\nCheck Stop Timeout\n')
        f.write(str(data['missedStopCheck']))
        f.write('\nLaser ON Timestamps\n')
        f.write(str(data['laserOn']))
        f.write('\n')
        f.close()
    
    def about(self):
        QMessageBox.about(self, "About",
"""Stop Signal Task Control Program

This program is a simple system for neuroscience research of behavior inhibition.

It may be used and modified with no restriction."""
)    
    
    def testRewardStart(self):
        self.connection.write('t')
    
    def testRewardEnd(self):
        self.connection.write('s')

    def testStopSignal(self):
        self.connection.write('f')

    def testLaserOn(self):
        self.connection.write('l')

    def testLaserOff(self):
        self.connection.write('x')


class NewTraining(QDialog, Ui_Dialog):
    def __init__(self):
        QDialog.__init__(self)
        Ui_Dialog.__init__(self)
        self.setupUi(self)

        #set constraints on QLineedits   
        self.gbaseline.setValidator(QIntValidator(1,500,self))
        self.gbaseline.textChanged.connect(self.check_lineedit_state)
        self.gbaseline.textChanged.emit(self.gbaseline.text())
        
        self.gSessionLength.setValidator(QIntValidator(1,500,self))
        self.gSessionLength.textChanged.connect(self.check_lineedit_state)
        self.gSessionLength.textChanged.emit(self.gSessionLength.text())
        
        self.blockLengthEdit.setValidator(QIntValidator(1,500,self))
        self.blockLengthEdit.textChanged.connect(self.check_lineedit_state)
        self.blockLengthEdit.textChanged.emit(self.blockLengthEdit.text())
        
        self.blockNumberEdit.setValidator(QIntValidator(1,10,self))
        self.blockNumberEdit.textChanged.connect(self.check_lineedit_state)
        self.blockNumberEdit.textChanged.emit(self.blockNumberEdit.text())
        
        self.gLH.setValidator(QIntValidator(100,30000,self))
        self.gLH.textChanged.connect(self.check_lineedit_state)
        self.gLH.textChanged.emit(self.gLH.text())
        
        self.gPunishment.setValidator(QIntValidator(1000,10000,self))
        self.gPunishment.textChanged.connect(self.check_lineedit_state)
        self.gPunishment.textChanged.emit(self.gPunishment.text())
        
        self.gReward.setValidator(QIntValidator(10,1000,self))
        self.gReward.textChanged.connect(self.check_lineedit_state)
        self.gReward.textChanged.emit(self.gReward.text())        
        
        self.blinkerFreq.setValidator(QIntValidator(5,100,self))
        self.blinkerFreq.textChanged.connect(self.check_lineedit_state)
        self.blinkerFreq.textChanged.emit(self.blinkerFreq.text())            
        
        self.stageComboBox.activated.connect(self.stageSelection)

        self.directionComboBox.activated.connect(self.directionSelection)
            
        self.data=dict()
        self.data['stage']=1
        self.data['direction']='l'
        
    
    def check_lineedit_state(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QValidator.Acceptable:
            color = '#c4df9b' # green
        elif state == QValidator.Intermediate:
            color = '#fff79a' # yellow
        else:
            color = '#f6989d' # red
        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)
   
    def stageSelection(self, stage):
        self.data['stage']=stage+1
        if stage <2 or stage==5:
            self.gStopPercent.setEnabled(False)
            self.blockLengthEdit.setEnabled(False)
            self.blockNumberEdit.setEnabled(False)
            self.gLH.setEnabled(False)
            self.gLaserFreq.setEnabled(False)
            self.gPulseDur.setEnabled(False)
            self.gLaserDur.setEnabled(False)
        elif stage==2:
            self.gStopPercent.setEnabled(False)
            self.blockLengthEdit.setEnabled(False)
            self.blockNumberEdit.setEnabled(False)
            self.gLH.setEnabled(True)
            self.gLaserFreq.setEnabled(False)
            self.gPulseDur.setEnabled(False)
            self.gLaserDur.setEnabled(False)
        elif stage==3:
            self.gStopPercent.setEnabled(True)
            self.blockLengthEdit.setEnabled(True)
            self.blockNumberEdit.setEnabled(True)
            self.gLH.setEnabled(True)
            self.gLaserFreq.setEnabled(False)
            self.gPulseDur.setEnabled(False)
            self.gLaserDur.setEnabled(False)
        elif stage==4:
            self.gStopPercent.setEnabled(True)
            self.blockLengthEdit.setEnabled(True)
            self.blockNumberEdit.setEnabled(True)
            self.gLH.setEnabled(True)
            self.gLaserFreq.setEnabled(True)
            self.gPulseDur.setEnabled(True)
            self.gLaserDur.setEnabled(True)

    def directionSelection(self, direction):
        if direction == 0:
            self.data['direction'] = 'l'
        else:
            self.data['direction'] = 'r'
        
    
    def getParameters(self):
  
        # configurations
        # if(self.direction_left.isChecked()):
        #     self.data['direction']='l'
        # else:
        #     self.data['direction']='r'
        
        self.data['baseline']=self.gbaseline.text()
        self.data['sessionLength']=self.gSessionLength.text()
        self.data['lh']=str(int(int(self.gLH.text())*1.024))
        self.data['reward']=str(int(int(self.gReward.text())*1.024))
        self.data['punishment']=str(int(int(self.gPunishment.text())*1.024))
        self.data['blinkerFreq']=self.blinkerFreq.text()
        self.data['isLaser']='0'
        if self.data['stage']<4 or self.data['stage']==6:
            self.data['stopPercent']='0'
            self.data['blockLength']='0'
            self.data['blockNumber']='0'
            self.data['laserFreq']='0'
            self.data['pulseDur']='0'
            self.data['laserDur']='0'
        elif self.data['stage']==4:
            self.data['stopPercent']=self.gStopPercent.text()
            self.data['blockLength']=self.blockLengthEdit.text()
            self.data['blockNumber']=self.blockNumberEdit.text()
            self.data['laserFreq']='0'
            self.data['pulseDur']='0'
            self.data['laserDur']='0'

        elif self.data['stage']==5:
            if int(self.data['baseline'])<20:
                print("Baseline better bigger than 20")
                self.data['baseline']='20'
            self.data['stopPercent']=self.gStopPercent.text()
            self.data['blockLength']=self.blockLengthEdit.text()
            self.data['blockNumber']=self.blockNumberEdit.text()
            self.data['laserFreq']=self.gLaserFreq.text()
            self.data['pulseDur']=str(int(int(self.gPulseDur.text())*1.024))
            self.data['laserDur']=str(int(int(self.gLaserDur.text())*1.024))

            if int(self.data['laserFreq'])>0 and int(self.data['pulseDur'])>0 and int(self.data['laserDur'])>0:
                self.data['isLaser']='1'
        
        return self.data

class MyHistCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=70):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)
        #self.axes.xaxis.set_tick_params(labelsize=8)
        #
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def update_figure(self, x):
        if(len(x)>1):
            x=x/1000
            self.axes.hist(x, color='c', alpha=0.5, bins=20) 
            self.axes.set_xlabel('Time (s)')
            self.axes.set_ylabel('count')
            self.draw()
    def reset(self):
        x = np.random.normal(size=10)
        self.axes.plot(list(range(10)),x)
        self.draw()
    
# main entry point of the script    
def main():
    speed = 115200   # communication speed
    port = 'COM3'   # port used for communication
            
    app = QApplication(sys.argv)
    window = mainWindow(port, speed)
    window.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    
    main()
