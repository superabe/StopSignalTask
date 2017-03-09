# -*- coding: utf-8 -*-
"""
Created on Fri May 15 18:27:47 2015

@author: lin
"""

import os

class Data(object):
    '''
    data encapsulation
    '''
    def __init__(self):
        self.temp_file_name = '.sst_data_temp'
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
        self.laser_on = []
        self.unicode_error = []
        self.data_length_error = []
        self.missed_data_error = []
        self.trial_num = []
        self.who_knows = []

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
            elif event == 'UnicodeError':
                self.unicode_error.append(timestamp)
            elif event == 'DataLengthError':
                self.data_length_error.append(timestamp)
            elif event == 'TN':
                self.trial_num.append(timestamp)
                if timestamp > 1:
                    return 0
            elif event == 'GE':
                pass
            elif event == 'SE':
                pass
            elif event == 'LE':
                pass
            elif event == 'S+':
                pass
            elif event == 'S-':
                pass
            else:
                if len(self.trial_num) > 0:
                    self.who_knows.append((self.trial_num[-1], data_in))
        return 1


    def get(self):
        '''
        return the all the list
        '''
        return {'pokeInL':self.poke_in_l, 'pokeOutL':self.poke_out_l, 'pokeInR':self.poke_in_r,
                'pokeOutR':self.poke_out_r, 'pokeInM':self.poke_in_m, 'pokeOutM':self.poke_out_m,
                'rewardStart':self.reward_start, 'stopSignalStart':self.stop_signal_start,
                'isRewarded':self.is_rewarded, 'trialType':self.trial_type[0:len(self.poke_in_l)],
                'SSDs':self.ssd, 'trialsSkipped':self.trials_skipped,
                'unicodeError':self.unicode_error, 'dataLengthError':self.data_length_error,
                'laserOn':self.laser_on, 'whoKnows':self.who_knows}

    def save(self, over_write=True):
        '''
        create a temp file and save the data
        used for data restore
        '''
        file_name = self.temp_file_name
        if not over_write:
            counter = 1
            while os.path.exists(file_name):
                file_name = file_name + str(counter)
                counter += 1

        data_to_write = self.get()

        with open(file_name, 'w') as temp_file:
            for name, value in data_to_write.items():
                temp_file.write('\n'+name+'\n')
                temp_file.write(str(value))

    def clear_temp(self):
        '''
        remove temp file
        '''
        if os.path.exists(self.temp_file_name):
            os.remove(self.temp_file_name)
