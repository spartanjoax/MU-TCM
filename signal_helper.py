# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 11:39:19 2023

@author: jjperalta
"""

import os
from fnmatch import fnmatch
import matplotlib.pyplot as plt
import numpy as np

import scipy.io
import scipy.signal
from statistics import mean
from scipy.stats import kurtosis, skew
import pywt

def get_file_list(root='.', pattern='*.*'):
    file_list = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            if fnmatch(name, pattern):
                file_list.append(os.path.join(path, name))
    return file_list

def load_file(file):
    mat = scipy.io.loadmat(file)
    for k in mat.keys():
        if type(mat[k]) == np.ndarray:
            if len(mat[k].shape) == 1:
                mat[k] = str(mat[k][0])
            elif mat[k].shape[0] == 1 and mat[k].shape[1]>1:
                mat[k] = mat[k][0]
            elif mat[k].shape[0] == 1:
                mat[k] = mat[k][0][0]
            else:
                mat[k] = mat[k].reshape((len(mat[k])))
    return mat

def drop_after_x(arr, x):
    # Find the first index where the value is greater than x
    if x > max(arr):
        index = len(arr)
    else:
        index = np.where(arr > x)[0][0]

    # Create a new array with all elements before the index
    new_arr = arr[:index]

    return new_arr

def drop_before_x(arr, x):
    # Find the first index where the value is greater than x
    if x < 0:
        index = 0
    else:
        index = np.where(arr < x)[0][0]

    # Create a new array with all elements before the index
    new_arr = arr[index:]

    return new_arr

def load_and_plot_file(file, freq_i=285, freq_e=50000, freq_e_high=1000000):
    mat = load_file(file)

    fig, axs = plt.subplots(6, 1, figsize=(20,30))
    label='RPM'
    signal=mat['SREAL']
    x_values=np.arange(len(signal))/freq_i
    axs[0].plot(x_values, signal, label=label)
    axs[0].legend(loc='lower left')
    
    rpm_avg = np.average(signal)    
    print('RPM promedio:', rpm_avg)
    
    label='TV2_S fuerzas'
    signal=mat['TV2_S']
    axs[1].plot(x_values, signal, label=label)
    axs[1].legend(loc='lower left')
    
    label='TV2_Z fuerzas'
    signal=mat['TV2_Z']
    axs[2].plot(x_values, signal, label=label)
    axs[2].legend(loc='lower left')
    
    label='TV51 PotenciaActiva'
    signal=mat['TV51']
    axs[3].plot(x_values, signal, label=label)
    axs[3].legend(loc='lower left')
    
    label='TV50 PowerFeedback'
    signal=mat['TV50']
    axs[4].plot(x_values, signal, label=label)
    axs[4].legend(loc='lower left')
    
    label='CV3_S'
    signal=mat['CV3_S']
    axs[5].plot(x_values, signal, label=label)
    axs[5].legend(loc='lower left')
    
    plt.tight_layout()
    plt.show()
        
    if 'Fx' in mat.keys():
        
        signal_end = len(mat['Fx'])
        
        while True:
            fig, axs = plt.subplots(5, 1, figsize=(20,25))
            label='Fx'
            signal=mat[label][:signal_end]
            x_values=np.arange(len(signal))/freq_e
            axs[0].plot(x_values, signal, label=label)
            axs[0].legend(loc='lower left')
            label='Fz'
            signal=mat[label][:signal_end]
            axs[1].plot(x_values, signal, label=label)
            axs[1].legend(loc='lower left')
            label='Ax'
            signal=mat[label][:signal_end]
            axs[2].plot(x_values, signal, label=label)
            axs[2].legend(loc='lower left')
            label='Az'
            signal=mat[label][:signal_end]
            axs[3].plot(x_values, signal, label=label)
            axs[3].legend(loc='lower left')
            label='AE_RMS'
            signal=mat[label][:int(signal_end/freq_e*freq_e_high)]
            x_values=np.arange(len(signal))/freq_e_high
            axs[4].plot(x_values, signal, label=label)
            axs[4].legend(loc='lower left')
            plt.tight_layout()
            plt.show()
            
            secs = input('Do you want to cut the signal from the end? Y or [N]: ')
            if secs.lower() == 'y':
                secs = input('Input from where to cut the signal in seconds: ')
                if secs != '':
                    signal_end=int(float(secs)*freq_e)
            else:
                break
        
        if signal_end != len(mat['Fx']):
            mat['Fx'] = mat['Fx'][:signal_end]
            mat['Fy'] = mat['Fy'][:signal_end]
            mat['Fz'] = mat['Fz'][:signal_end]
            mat['Ax'] = mat['Ax'][:signal_end]
            mat['Ax'] = mat['Ax'][:signal_end]
            mat['Ax'] = mat['Ax'][:signal_end]
            mat['AE_F'] = mat['AE_F'][:int(signal_end/freq_e*freq_e_high)]
            mat['AE_RMS'] = mat['AE_RMS'][:int(signal_end/freq_e*freq_e_high)]
    
    return mat,rpm_avg


def clean_peaks(signal, peaks, freq):
    curr_max = peaks[0]
    curr_value = signal[peaks[0]]
    cleaned_peaks = []
    
    for i in range(1, len(peaks)):
        if peaks[i] - peaks[i - 1] > freq:
            cleaned_peaks.append(curr_max)            
            curr_max = peaks[i]
            curr_value = signal[peaks[i]]
        elif signal[peaks[i]] > curr_value:
            curr_max = peaks[i]
            curr_value = signal[peaks[i]]
    #Append last peak found
    cleaned_peaks.append(curr_max)
    
    return np.array(cleaned_peaks)

def clean_peaks_mid(signal, peaks, dist):
    curr_ini = peaks[0]
    curr_last = peaks[0]
    cleaned_peaks = []
    
    for i in range(1, len(peaks)):
        if peaks[i] - peaks[i - 1] > dist:
            cleaned_peaks.append(int(mean([curr_ini, curr_last])))
            curr_ini = peaks[i]
            curr_last = peaks[i]
        curr_last = peaks[i] 
    #Append last peak found
    cleaned_peaks.append(int(mean([curr_ini, curr_last])))
    
    return np.array(cleaned_peaks)

def calcular_freq(signal, label, height, freq, rpm, calc='avg', peaks_ref=None):
    print('^^^^^^^^')
    print(f'Searching for {calc} peaks in signal {label} with length {len(signal)}, initial height of {height}, frequency {freq}, and RPM {rpm}')
    
    if peaks_ref is None:
        peaks, _ = scipy.signal.find_peaks(signal, height=height)
    else:
        peaks = peaks_ref
        
    avg_h = 0
    max_h = 0
    min_h = 0
    freq_c = freq
        
    print('Qty of peaks before cleaning:',len(peaks))
    if len(peaks) > 0:
        avg = np.average(np.diff(peaks))
        print('Average distance between peaks (ADBP) before cleaning:',avg)
        
        if freq < 500:
            if rpm < 200:
                dist = 32
            elif rpm < 400:
                dist = 16
            else:
                dist = 8
        elif freq < 100000:
            if rpm < 200:
                dist = 5000
            elif rpm < 400:
                dist = 2500
            else:
                dist = 1250
        else:
            if rpm < 200:
                dist = 100000
            elif rpm < 400:
                dist = 50000
            else:
                dist = 25000
        
        plt.figure(figsize=(20,6))
        plt.plot(signal, label=label + "_all")
        plt.scatter(peaks,signal[peaks], color = 'hotpink',zorder=10)
        plt.legend(loc='lower left')
        plt.show()
        
        if peaks_ref is None:
            peaks_max = clean_peaks(signal, peaks, dist)
            
            plt.figure(figsize=(20,6))
            plt.plot(signal, label=label + "_max")
            plt.scatter(peaks_max,signal[peaks_max], color = 'hotpink',zorder=10)
            plt.legend(loc='lower left')
            plt.show()
    
        avg_h = np.average(signal[peaks])
        max_h = np.max(signal[peaks])
        min_h = np.min(signal[peaks])
        print('Avg value of peaks:',avg_h)
        print('Max value of peaks:',max_h)
        print('Min value of peaks:',min_h)
        
        if calc == 'max':
            peaks = peaks_max
        else:
            peaks = clean_peaks_mid(signal, peaks, dist)
            print('Qty of peaks after cleaning:',len(peaks))
            
        plt.figure(figsize=(20,6))
        plt.plot(signal, label=label + "_avg")
        plt.scatter(peaks,signal[peaks], color = 'hotpink',zorder=10)
        plt.legend(loc='lower left')
        plt.show()
        
        qty_drop_i = 0
        qty_drop_e = 0
        
        while True:
            secs = input('How many peaks should be dropped from the start? [0]:')
            if secs != '':
                qty_drop_i=int(secs)
                peaks_tmp = peaks[qty_drop_i:]
                
                plt.figure(figsize=(20,6))
                plt.plot(signal, label=label + "_avg")
                plt.scatter(peaks_tmp,signal[peaks_tmp], color = 'hotpink',zorder=10)
                plt.legend(loc='lower left')
                plt.show()
            else:
                break
                
        while True:
            secs = input('How many peaks should be dropped from the end? [0]:')
            if secs != '':
                qty_drop_e=int(secs)
                peaks_tmp = peaks[qty_drop_i:len(peaks) - qty_drop_e]
                
                plt.figure(figsize=(20,6))
                plt.plot(signal, label=label + "_avg")
                plt.scatter(peaks_tmp,signal[peaks_tmp], color = 'hotpink',zorder=10)
                plt.legend(loc='lower left')
                plt.show()
            else:
                break
            
        if qty_drop_i > 0:
            peaks = peaks[qty_drop_i:]
        if qty_drop_e > 0:
            peaks = peaks[:len(peaks) - qty_drop_e]
        
        avg = np.average(np.diff(peaks))
        min = np.min(np.diff(peaks))
        max = np.max(np.diff(peaks))
        freq_c=int(rpm/60*avg)
        
        print('Final qty of peaks after cleaning:',len(peaks))
        print('Distance between first and last peak:',np.max(peaks) - np.min(peaks))
        print(f'Seconds between first and last peak @ {freq_c} Hz:',(np.max(peaks) - np.min(peaks))/freq_c)
        print('>>>> Stats:')
        print('Min distance between peaks:',min)
        print('Avg distance between peaks:',avg)
        print('Max distance between peaks:',max)
        print(f'Revolutions per minute (RPM): {rpm} - Revolutions per second (RPM/60): {rpm/60}')
        print('Min calculated sampling frequency (RPM/60*DPEP):',rpm/60*min, "Factor:",(rpm/60*min)/freq)
        print('Avg calculated sampling frequency (RPM/60*DPEP):',rpm/60*avg, "Factor:",(rpm/60*avg)/freq)
        print('Max calculated sampling frequency (RPM/60*DPEP):',rpm/60*max, "Factor:",(rpm/60*max)/freq)
        print('^^^^^^^^')

    return peaks, freq_c, avg_h, max_h, min_h

def rms(values):
    return np.sqrt(sum(values**2)/len(values))

def std(x): 
    return np.std(x)

def spec_kurt(values, sampling_rate):
    (f, S)= scipy.signal.welch(values, sampling_rate, nperseg=4*1024)
    kurt = kurtosis(abs(S))    
    return kurt

def spec_skew(values, sampling_rate):
    (f, S)= scipy.signal.welch(values, sampling_rate, nperseg=4*1024)
    skewness = skew(abs(S))    
    return skewness

def coeff_energy(values):
    E=[]
    for key, values in values.items():
        ene = 0
        for i in range(len(values)):
            ene += values[i]**2
        E.append(ene / len(values) if len(values) > 0 else 0)
    return E

def wavelet_energy(values, mother_wavelet, wavelet_level):        
    (data, coeff_d) = pywt.dwt(values, mother_wavelet)
    coeff = {"D1": coeff_d}
    
    for i in range(1, wavelet_level):
        (data, coeff_d) = pywt.dwt(data, mother_wavelet)
        coeff["D"+str(i+1)] = coeff_d
        
    coeff['A'+str(wavelet_level)] = data
    energy = coeff_energy(coeff)
    return max(energy)