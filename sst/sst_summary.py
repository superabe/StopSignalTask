'''
Created on 2014-1-1

Methods for preliminary data analysis.

@author: lin

@email: superabee@gmail.com
'''
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.stats import skewtest
from sst.preprocess import loadData, calSSRT2
#from pandas import DataFrame


def calCR(trialType, isRewarded):
    '''
    Calculate correct rate of go trials and stop trials separately.

    Parameters
    ----------
    trialType: trialType of each trial. "1": go trials  "2" or bigger: stop trials
    isRewarded: the trial is rewarded or not. "1": yes "0": no

    Returns
    -------
    correctRate: Dictionary
        return a Dictionary contains correct rates of go trials and stop trials.


    '''
    correct1 = 0
    wrong1 = 0
    correct2 = 0
    wrong2 = 0
    if len(trialType) == len(isRewarded):
        if len(trialType) == 0:
            print('Output data equals zero!')
            return {'GoTrial':0, 'StopTrial':0}
        for i, _ in enumerate(trialType):
            if trialType[i] == 1 and isRewarded[i] == 0:
                wrong1 += 1
            elif trialType[i] == 1 and isRewarded[i] == 1:
                correct1 += 1
            elif trialType[i] != 1 and isRewarded[i] == 0:
                wrong2 += 1
            else:
                correct2 += 1
        if (correct2+wrong2) > 0 and (correct1+wrong1) > 0:
            return {'GoTrial': format(float(correct1)/(correct1+wrong1), '.2f'),
                    'StopTrial': format(float(correct2)/(correct2+wrong2), '.2f')}
        elif (correct1+wrong1) > 0 and (correct2+wrong2) == 0:
            return {'GoTrial': format(float(correct1)/(correct1+wrong1), '.2f'),
                    'StopTrial': '0'}
        elif (correct2+wrong2) > 0 and (correct1+wrong1) == 0:
            return {'GoTrial': '0',
                    'StopTrial': format(float(correct2)/(correct2+wrong2), '.2f')}
        else:
            return {'GoTrial': '0', 'StopTrial': '0'}

    elif len(trialType) == 0: #In training stage3, the length of trialType equals zero.
        return {'GoTrial': format(float(sum(isRewarded))/len(isRewarded), '.2f'),
                'StopTrial':'0'}
    else:
        print('Output data length is unequal! Cannot calculate the correct rate.')
        return {'GoTrial': '0', 'StopTrial': '0'}



def calRT(list1, list2):
    '''
    Caluculate the Go Reaction Time in Go Trial (From L to R or the other way around)
    Usually, this function is called automatically after every training session.
    The result will be store in the ouput file.

    Parameters
    ----------
    list1: Timestamps when rat leaves left or right
    list2: Timestamps when rat poke into the other hole.
    baseline: The number of trials will be excluded for further analysis.

    Returns
    -------
    calRT : numpy.ndarray
        Return an array of 1-D ndarray contains all the Go reaction time

    '''
    #Store two lists temporarily
    temp1 = np.array(list1)
    temp2 = np.array(list2)
    #Two lists should be of equal length
    if len(temp1) != len(temp2):
        print('Data length is not equal!')
        return [0]
    elif len(temp1) == 0:
        print('Data length equals zero!')
        return [0]
    else:
        #Delete elements whose values are zero.
        #Because zero values mean error trials or stop trials
        k = [i for i in range(len(temp1)) if temp1[i] != 0 and temp2[i] != 0]
        if len(k) > 0:
            temp1 = temp1[k]
            temp2 = temp2[k]
            if temp1[0] > temp2[0]:
                rt = temp1 - temp2
            else:
                rt = temp2 - temp1
            # change rt from self-define millis to seconds
            return rt
        else:
            return []


def plotRTD(rt,baseline=20, col='green', num_bins=30):
    '''
    Plot the Go Reaction Time Distribution

    Parameter
    ---------
    rt: The Go Reaction Time
    col: The Facecolor of the histogram
    num_bins: The bins of the histogram

    '''
    rt = rt[(baseline+1):]
    # the histogram of the data
    n, bins, patches = plt.hist(rt, facecolor=col, bins=num_bins, alpha=0.5)
    # add a 'best fit' line using spline method.
    bins = bins[:-1] + (bins[1]-bins[0]) / 2
    f = UnivariateSpline(bins, n, s=50)
    plt.plot(bins, f(bins), 'r--')
    plt.title('RT Distribution', fontsize='xx-large')
    plt.xlabel('RT', fontsize='x-large')
    plt.ylabel('Frequency', fontsize='x-large')
    plt.show()

def returnSSRT(filename):
    '''
    '''
    data = loadData(filename)['df']
    if data.shape[0] > 320:
        ssrt = calSSRT2(data)
        return ssrt
    else:
        return 0


def median(list1):
    '''
    Calculate the median of a list array.
    '''
    if len(list1) < 1:
        return None
    else:
        list1.sort()
        k = len(list1) / 2
        if len(list1) % 2 == 0:
            return (list1[k-1] + list1[k]) / 2
        else:
            return list1[k]
