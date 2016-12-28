#This module contains preprocess functions of stop signal task result.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def loadData(file_name):
    data = {}
    with open(file_name, 'r') as f:
        print(f.readline())
        general_message = f.readline()
        print(general_message)
        data['General Message'] = general_message  # the first two line: general information
        lines = f.readlines()
        for i in range(len(lines)):
            if i%2==0:
                if len(lines[i+1])>2:
                    data[lines[i][:-1]] = [s.strip() for s in lines[i+1][1:-2].split(',')]
                else:
                    data[lines[i][:-1]] = []

    df = pd.DataFrame({'PokeOutR':data['PokeOutR'], 'PokeInR':data['PokeInR'],
                        'PokeInL':data['PokeInL'], 'PokeOutL':data['PokeOutL'],
                        'IsRewarded':data['IsRewarded'],
                        'TrialType':data['TrialType'],
                        'PokeInM':data['PokeInM'],
                        'StopSignalStart':np.zeros(len(data['PokeInM'])),
                        'SSDs':np.zeros(len(data['PokeInM'])),
                        'StopSkipped':np.zeros(len(data['PokeInM']))},
                        dtype=float)
    if len(data['Trials Skipped'])>0:
        stop_skipped = np.array(data['Trials Skipped'], dtype=int)-1 # index starts from 0.
        df.ix[stop_skipped, 'TrialType'] = 1
    if len(data['StopSignalStart'])>0:
        df.ix[df['TrialType']==2, 'StopSignalStart'] = np.array(data['StopSignalStart'], dtype=float)
        df.ix[df['TrialType']==2, 'SSDs'] = np.array(data['SSDs'], dtype=float)
    return_data = {'info':data['General Message'],
                   'df':df}
                   #'laser':np.array(data['Laser ON Timestamps'], dtype=float)}

    return return_data

def calCorRate(data, baseline=20, end=320):
    data = data.iloc[baseline:end]
    total_go = sum(data.ix[data['TrialType']==1, 'TrialType'])
    correct_go = sum(data.ix[(data['TrialType']==1) & (data['IsRewarded']==1), 'TrialType'])
    total_stop = sum(data.ix[data['TrialType']==2, 'TrialType'])
    correct_stop = sum(data.ix[(data['TrialType']==2) & (data['IsRewarded']==1), 'TrialType'])
    return (correct_go/total_go, correct_stop/total_stop)

def calSSRT(data, baseline=20, end=320):#left-right-middle
    stopcorrect=calCorRate(data, baseline, end)[1]
    data = data.iloc[baseline:end]
    correct_go = data.ix[(data['TrialType']==1) & (data['IsRewarded']==1)]

    pokeR = pd.Series(correct_go['PokeInR'])
    pokeL = pd.Series(correct_go['PokeInL'])

    if pokeR.iloc[0] > pokeL.iloc[0]:
        gort = correct_go['PokeInR'] - correct_go['PokeOutL']
    else:
        gort = correct_go['PokeInL'] - correct_go['PokeOutR']


    ssd=[i for i in data['SSDs'] if i>0]
    quantile_gort=1-stopcorrect
    se=sorted(gort)
    len_gort=len(gort)
    T= se[int(len_gort*quantile_gort)]
    ssd_mean=np.mean(ssd)
    ssrt=T-ssd_mean
    return ssrt

def calSSRT2(data, baseline=20, block_length=100, block_num=3, isCorrect=False):
    # remove baseline
    data = data.iloc[baseline:]

    ssrts = []
    # calculate SSRT block wise
    for i in range(block_num):
        temp_data = data.ix[i*block_length:(i+1)*block_length]
        ssrts.append(calSSRT(temp_data, baseline=0,end=block_length))
    return sum(ssrts)/len(ssrts)
