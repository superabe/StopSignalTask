# -*- coding: utf-8 -*-
"""
Created on Fri May 15 18:27:47 2015

@author: lin
"""

class Data(object):
    '''
    data encapsulation
    '''
    def __init__(self):
        self.poke_in_l = []
        self.poke_out_l = []
        self.poke_in_r = []
        self.poke_out_r = []
        self.poke_in_m = []
        self.poke_out_m = []
        self.reward_start = []
        self.stop_signal_start = []
        self.is_rewarded = []
        self.trial_type = []
        self.ssd = []
        self.trials_skipped = []
        self.missed_data = []
        self.missed_stop_check = []
        self.laser_on = []

    def write(self, data_in):
        '''
        append timestamps of different events
        '''
        print(data_in)
        if len(data_in) == 2:
            event = data_in[0]
            timestamp = data_in[1]
            if event == 'IL':
                self.poke_in_l.append(timestamp/1.024)
            elif event == 'OL':
                self.poke_out_l.append(timestamp/1.024)
            elif event == 'IM':
                self.poke_in_m.append(timestamp/1.024)
            elif event == 'OM':
                self.poke_out_m.append(timestamp/1.024)
            elif event == 'IR':
                self.poke_in_r.append(timestamp/1.024)
            elif event == 'OR':
                self.poke_out_r.append(timestamp/1.024)
            elif event == 'SS':#stop signal start
                self.stop_signal_start.append(timestamp/1.024)
            elif event == 'RS':#reward start
                self.reward_start.append(timestamp/1.024)
                if timestamp == 0:
                    self.is_rewarded.append(0)
                else:
                    self.is_rewarded.append(1)
            elif event == 'TT':#trialType
                self.trial_type.append(int(timestamp))
            elif event == 'SD':
                self.ssd.append(timestamp/1.024)
            elif event == 'TS':#trialSkipped
                self.trials_skipped.append(int(timestamp))
            elif event == 'L':#Laser on timestamps
                self.laser_on.append(timestamp/1.024)
            elif event == 'Error':
                self.missed_data.append(data_in)
            elif event == 'TN' and timestamp > 1:
                return 0
        return 1


    def get(self):
        '''
        return the all the list
        '''
        return {'pokeInL':self.poke_in_l, 'pokeOutL':self.poke_out_l, 'pokeInR':self.poke_in_r,
                'pokeOutR':self.poke_out_r, 'pokeInM':self.poke_in_m, 'pokeOutM':self.poke_out_m,
                'rewardStart':self.reward_start, 'stopSignalStart':self.stop_signal_start,
                'isRewarded':self.is_rewarded, 'trialType':self.trial_type[0:len(self.poke_in_l)],
                'SSDs':self.ssd, 'trialsSkipped':self.trials_skipped, 'missedData':self.missed_data,
                'missedStopCheck':self.missed_stop_check, 'laserOn':self.laser_on}
