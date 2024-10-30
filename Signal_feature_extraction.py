# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 10:09:03 2023

@author: jjperalta
"""

import os
import signal_helper as sh
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import ntpath
from scipy.stats import kurtosis, skew

mother_wavelet = 'db8'
wavelet_level = 10

pre_sync = []

x_tick_qty = 40
y_tick_qty = 10

files = sh.get_file_list(root='../Optitwin synced', pattern='*.mat')
print(f'Cantidad de archivos encontrados: {len(files)}')

height_rpm=[-196,-396.5,-794.5]
height=2400
height_e=0

signals_cnc=[
    'SREAL',
    'CV3_S',
    'CV3_X',
    'CV3_Y',
    'CV3_Z',
    'TV2_S',
    'TV2_X',
    'TV2_Y',
    'TV2_Z',
    'TV50',
    'TV51',
    'FREAL'
    ]
signals_ext=[
    'Ax',
    'Ay',
    'Az',
    'Fx',
    'Fy',
    'Fz',
    'AE_F',
    'AE_RMS'
    ]

for file in files:
    print('====================================================')
    print('Analyzing file ', file)
    
    json_file = file.replace('.mat','_stats.json')
    
    if os.path.exists(json_file):
        print('File already exists: ', json_file)        
        with open(json_file, "r") as f:
            file_stats = json.load(f)              
        pre_sync.append(file_stats)
        continue
    else:
        print('File will be saved at: ', json_file)
        
    mat, rpm_avg = sh.load_and_plot_file(file,freq_i=1,freq_e=1)
    file = ntpath.basename(file)
    
    if rpm_avg < 200:
        height=height_rpm[0]
    elif rpm_avg < 400:
        height=height_rpm[1]
    else:
        height=height_rpm[2]
        
    file_stats = {
        '_file_name' : file,
        'RPM_avg' : rpm_avg,
        'material' : mat['WorkpieceMaterial'],
        'Vc' : int(mat['Vc']),
        'fz' : mat['fz'],
        'ap' : mat['ap'],
        'ae' : mat['ae'],
        'VB' : mat['VB']
        }
    
    fig, axs = plt.subplots(6, 1, figsize=(20,30))
    axs[0].plot(mat['SREAL'], label='SREAL')
    axs[0].legend(loc='upper left')
    axs[1].plot(mat['TV50_S'], label='TV50_S')
    axs[1].legend(loc='upper left')
    axs[2].plot(mat['TV2_Z'], label='TV2_Z')
    axs[2].legend(loc='upper left')
    
    if 'AE_F' in mat.keys():
        axs[3].plot(mat['Fz'], label='Fz')
        axs[3].legend(loc='upper left')
        axs[4].plot(mat['Az'], label='Az')
        axs[4].legend(loc='upper left')        
        axs[5].plot(mat['AE_RMS'], label='AE_RMS')
        axs[5].legend(loc='upper left')
    plt.tight_layout()
    plt.show()
    
    label = ''
    
    print('************************** CNC Signals')
    start = 0
    end = len(mat['SREAL'])
    peaks_cnc = []
    peaks_ext = []
    
    for label in signals_cnc:
        print(f'========== Analysing {label}')
                
        signal=mat[label]
        length_to_peak=0
        
        fig, axs = plt.subplots(2, 1, figsize=(20,20))
        axs[0].plot(signal, label=label+'_full')
        axs[0].legend(loc='lower left')
        y_min, y_max = axs[0].get_ylim()
        skip = (y_max - y_min) / y_tick_qty
        axs[0].set_yticks(np.arange(y_min, y_max + skip, skip))
        for y in np.arange(y_min, y_max+skip, skip):
            axs[0].axhline(y=y, color='lightgrey', linestyle='-', zorder=0)
        x_min, x_max = axs[0].get_xlim()
        skip = (x_max - x_min) / x_tick_qty
        axs[0].set_xticks(np.arange(x_min, x_max + skip, skip))
        for x in np.arange(x_min, x_max+skip, skip):
            axs[0].axvline(x=x, color='lightgrey', linestyle='-', zorder=0)
            
        axs[1].plot(signal[start:end], label=label+'_start to end')
        axs[1].legend(loc='lower left')
        y_min, y_max = axs[1].get_ylim()
        skip = (y_max - y_min) / y_tick_qty
        axs[1].set_yticks(np.arange(y_min, y_max + skip, skip))
        for y in np.arange(y_min, y_max+skip, skip):
            axs[1].axhline(y=y, color='lightgrey', linestyle='-', zorder=0)
        x_min, x_max = axs[1].get_xlim()
        skip = (x_max - x_min) / x_tick_qty
        axs[1].set_xticks(np.arange(x_min, x_max + skip, skip))
        for x in np.arange(x_min, x_max+skip, skip):
            axs[1].axvline(x=x, color='lightgrey', linestyle='-', zorder=0)
        plt.show()
        
        ask_range = True
        ask_peaks = True
        
        if (start != 0 or end != len(signal)) and len(peaks_cnc) > 0:
            secs = input(f'Use the same start ({start}) and end ({end}) as previous signals? [Y] or N: ')
            if secs.lower() != 'n':
                signal=signal[start:end]
                ask_range = False
            else:
                start = 0
                end = len(signal)
        
        while ask_range:            
            print(f'Current analysis is from {start} to {end} with length {len(signal)}')
            
            secs = input('Select new range for analysing the signal? Y or [N]: ')
            if secs.lower() == 'y':
                signal=mat[label]
                
                secs = input('Start of the signal analysis? >=[0]: ')
                start = int(secs) if secs != '' else 0 
                
                secs = input(f'End of the signal analysis? <=[{len(signal)}]: ')
                end = int(secs) if secs != '' else len(signal)
                
                signal = signal[start:end]
                
                plt.figure(figsize=(20,6))
                plt.plot(signal, label=label)
                plt.legend(loc='lower left')
                y_min, y_max = plt.ylim()
                skip = (y_max - y_min) / 10
                for y in np.arange(y_min, y_max+skip, skip):
                    plt.axhline(y=y, color='lightgrey', linestyle='-', zorder=0)
                x_min, x_max = plt.xlim()
                skip = (x_max - x_min) / 20
                print(f'X_min {x_min} - x_max {x_max} - skip {skip}')
                for x in np.arange(x_min, x_max+skip, skip):
                    plt.axvline(x=x, color='lightgrey', zorder=1)
                plt.show()
            else:
                break
            
        file_stats[f'{label}_start'] = start
        file_stats[f'{label}_end'] = end
        
        counter = 0
        print(f'Extracting features from at {start} to end at {end} for {label} with length {len(signal)}')
        
        file_stats[f'{label}_rms'] = sh.rms(signal)
        file_stats[f'{label}_var'] = np.var(signal)
        file_stats[f'{label}_max'] = float(np.max(signal))
        file_stats[f'{label}_kurt'] = kurtosis(signal)
        file_stats[f'{label}_skew'] = skew(signal)
        file_stats[f'{label}_ptp'] = float(np.ptp(signal))
        file_stats[f'{label}_speckurt'] = sh.spec_kurt(signal, 250)
        file_stats[f'{label}_specskew'] = sh.spec_skew(signal, 250)
        file_stats[f'{label}_wavenergy'] = sh.wavelet_energy(signal,mother_wavelet,wavelet_level)
        
    if 'AE_F' in mat.keys():
        print('************************** External signals')
        freq = 50000
        start = int(start / 250 * freq)
        end = int(end / 250 * freq)
        
        for label in signals_ext.keys():
            print(f'========== Analysing {label}')
            
            if label == 'AE_F':
                start = int(start / freq * 1000000)
                end = int(end / freq * 1000000)
                freq = 1000000
                
            signal=mat[label]
        
            fig, axs = plt.subplots(2, 1, figsize=(20,20))
            axs[0].plot(signal, label=label+'_full')
            axs[0].legend(loc='lower left')
            y_min, y_max = axs[0].get_ylim()
            skip = (y_max - y_min) / y_tick_qty
            axs[0].set_yticks(np.arange(y_min, y_max + skip, skip))
            for y in np.arange(y_min, y_max+skip, skip):
                axs[0].axhline(y=y, color='lightgrey', linestyle='-', zorder=0)
            x_min, x_max = axs[0].get_xlim()
            skip = (x_max - x_min) / x_tick_qty
            axs[0].set_xticks(np.arange(x_min, x_max + skip, skip))
            for x in np.arange(x_min, x_max+skip, skip):
                axs[0].axvline(x=x, color='lightgrey', linestyle='-', zorder=0)
                
            axs[1].plot(signal[start:end], label=label+'_start to end')
            axs[1].legend(loc='lower left')
            y_min, y_max = axs[1].get_ylim()
            skip = (y_max - y_min) / y_tick_qty
            axs[1].set_yticks(np.arange(y_min, y_max + skip, skip))
            for y in np.arange(y_min, y_max+skip, skip):
                axs[1].axhline(y=y, color='lightgrey', linestyle='-', zorder=0)
            x_min, x_max = axs[1].get_xlim()
            skip = (x_max - x_min) / x_tick_qty
            axs[1].set_xticks(np.arange(x_min, x_max + skip, skip))
            for x in np.arange(x_min, x_max+skip, skip):
                axs[1].axvline(x=x, color='lightgrey', linestyle='-', zorder=0)
            plt.show()
                
            ask_range = True
            ask_peaks = True
            
            if (start != 0 or end != len(signal)) and len(peaks_ext) > 0:                
                secs = input(f'Use the same start ({start}) and end ({end}) as previous signals? [Y] or N: ')
                if secs.lower() != 'n':
                    signal=signal[start:end]
                    ask_range = False
                else:
                    start = 0
                    end = len(signal)
            
            while ask_range:            
                print(f'Current analysis is from {start} to {end} with length {len(signal)}')
                
                secs = input('Select new range for analysing the signal? Y or [N]: ')
                if secs.lower() == 'y':
                    signal=mat[label]
                    
                    secs = input('Start of the signal analysis? [0]: ')
                    start = int(secs) if secs != '' else 0 
                    
                    secs = input(f'End of the signal analysis? [{len(signal)}]: ')
                    end = int(secs) if secs != '' else len(signal)
                    
                    signal = signal[start:end]
                    
                    plt.figure(figsize=(20,6))
                    plt.plot(signal, label=label)
                    plt.legend(loc='lower left')
                    y_min, y_max = plt.ylim()
                    skip = (y_max - y_min) / 10
                    for y in np.arange(y_min, y_max+skip, skip):
                        plt.axhline(y=y, color='lightgrey', linestyle='-', zorder=0)
                    x_min, x_max = plt.xlim()
                    skip = (x_max - x_min) / 20
                    print(f'X_min {x_min} - x_max {x_max} - skip {skip}')
                    for x in np.arange(x_min, x_max+skip, skip):
                        plt.axvline(x=x, color='lightgrey', linestyle='-', zorder=0)
                    plt.show()
                else:
                    break
                
            file_stats[f'{label}_start'] = start
            file_stats[f'{label}_end'] = end
            
            counter = 0
            freq=file_stats['Hz_AE' if 'AE' in label else 'Hz_F']
            print(f'Extracting features from start at {start} to end at {end} for {label} with length {len(signal)}')
                
            file_stats[f'{label}_rms'] = sh.rms(signal)
            file_stats[f'{label}_var'] = np.var(signal)
            file_stats[f'{label}_max'] = float(np.max(signal))
            file_stats[f'{label}_kurt'] = kurtosis(signal)
            file_stats[f'{label}_skew'] = skew(signal)
            file_stats[f'{label}_ptp'] = float(np.ptp(signal))
            file_stats[f'{label}_speckurt'] = sh.spec_kurt(signal, freq)
            file_stats[f'{label}_specskew'] = sh.spec_skew(signal, freq)
            file_stats[f'{label}_wavenergy'] = sh.wavelet_energy(signal,mother_wavelet,wavelet_level)
        
    secs = input('Flag file? Y or [N]: ')
    if secs.lower() == 'y':
        file_stats['flagged'] = True
    
    pre_sync.append(file_stats)
    
df = pd.DataFrame(pre_sync)
df.to_csv('signals_stats.csv',sep=';',decimal='.')
