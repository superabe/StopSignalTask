# -*- coding: utf-8 -*-
"""
Created on Fri May 15 18:27:47 2015

@author: lin
"""

class Data:
    def __init__(self):
        self.pokeInL = []
        self.pokeOutL = []
        self.pokeInR = []
        self.pokeOutR = []
        self.pokeInM = []
        self.pokeOutM = []
        self.rewardStart = []
        self.stopSignalStart = []
        self.isRewarded = []
        self.trialType = []
        self.SSDs = []
        self.trialsSkipped = []
        self.missedData = []
        self.missedStopCheck = []
        
    def write(self,incomingData):
        # append timestamps of different events
        data=incomingData.split(',')
        if(len(data)>1):
            try:
                event=str(data[0])
                t=float(data[1])
            except ValueError:
                event='Missing Data'
                t=str(data[0])+','+str(data[1])
            print((event, t))
            if(event=='IL'):
                self.pokeInL.append(t/1.024)
            elif(event=='OL'):
                self.pokeOutL.append(t/1.024)
            elif(event=='IM'):
                self.pokeInM.append(t/1.024)
            elif(event=='OM'):
                self.pokeOutM.append(t/1.024)
            elif(event=='IR'):
                self.pokeInR.append(t/1.024)
            elif(event=='OR'):
                self.pokeOutR.append(t/1.024)
            elif(event=='SS'):#stop signal start
                self.stopSignalStart.append(t/1.024)
            elif(event=='RS'):#reward start
                self.rewardStart.append(t/1.024)
                if(t==0):
                    self.isRewarded.append(0)
                else:
                    self.isRewarded.append(1)
            elif(event=='TT'):#trialType
                self.trialType.append(int(t))
            elif(event=='SSD'):
                self.SSDs.append(t/1.024)
            elif(event=='TS'):#trialSkipped
                self.trialsSkipped.append(int(t))
            elif(event=='Missing Data'):
                self.missedData.append(t)
            elif(event=='check stop timeout'):
                self.missedStopCheck.append(t)
            elif(event=='trialNum' and t>1):
                return 0
        return 1
            
                    
    def getData(self):
        return {'pokeInL':self.pokeInL,'pokeOutL':self.pokeOutL,'pokeInR':self.pokeInR,
                'pokeOutR':self.pokeOutR,'pokeInM':self.pokeInM,'pokeOutM':self.pokeOutM,
                'rewardStart':self.rewardStart,'stopSignalStart':self.stopSignalStart,
                'isRewarded':self.isRewarded,'trialType':self.trialType[0:len(self.pokeInL)],
                'SSDs':self.SSDs,'trialsSkipped':self.trialsSkipped,'missedData':self.missedData,
                'missedStopCheck':self.missedStopCheck}
