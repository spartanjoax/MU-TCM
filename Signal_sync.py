# -*- coding: utf-8 -*-
"""
Created on Tue Oct 10 17:52:32 2023

@author: jjperalta
"""

import os
import signal_helper as sh
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import ntpath

import scipy.io
import scipy.signal

folder_from = 'Optitwin unified'
folder_to = 'Optitwin synced'

pre_sync = []

files = sh.get_file_list(root=folder_from, pattern='*.mat')
print(f'File quantity: {len(files)}')

height_rpm=[-196,-396.5,-794.5]
height=2400
height_e=0

for file in files:
    print('====================================================')
    print('Analyzing file: ', file)
    
    output = folder_to + '/' + ntpath.basename(file)
    json_file = output.replace('.mat','.json')
    
    if os.path.exists(output):
        print('File already exists: ', output)        
        with open(json_file, "r") as f:
            file_peaks = json.load(f)
        pre_sync.append(file_peaks)
        continue
    else:
        print('File will be saved at: ', output)
    
    mat, rpm_avg = sh.load_and_plot_file(file)
    
    if rpm_avg < 200:
        height=height_rpm[0]
    elif rpm_avg < 400:
        height=height_rpm[1]
    else:
        height=height_rpm[2]
    
    file_peaks = {
        'file_name' : file,
        'RPM_avg' : rpm_avg
        }
    
    if 'AE_F' in mat.keys():
        file_peaks['Hz_AE'] = round(1/(np.average(np.diff(mat['time1']))), 0)
        file_peaks['Hz_F'] = round(1/(np.average(np.diff(mat['time2']))), 0)        
        freq=file_peaks['Hz_F']
    
    label = ''
    factor = 1
    
    print('************************** CNC Signals')
    
    while label == '':
        secs = input('Which internal signal will be used? [0] (SREAL), 1 (TV2_S), 2 (TV2_Z), 3 (TV51) or 4 (TV50): ')
        if secs != "":
            secs = int(secs)
        else:
            secs = 0
            
        if secs == 0:
            label = 'SREAL'
            factor = -1 #SREAL has factor of -1 since we care more for the minimum peaks, as the RPMs are reduced when coming into contact with the material
        elif secs == 1:
            label = 'TV2_S'
        elif secs == 2:
            label = 'TV2_Z'
        elif secs == 3:
            label = 'TV51'
        elif secs == 4:
            label = 'TV50'
            
    file_peaks['i_signal'] = label
            
    freq_cnc=250
    signal=mat[file_peaks['i_signal']]*factor
    length_to_peak=0
    
    file_peaks['i_start'] = 0
    file_peaks['i_end'] = len(signal)
    
    while True:        
        peaks_cnc, freq_cnc, avg_h, max_h, min_h = sh.calcular_freq(signal, label, height, freq_cnc, rpm_avg)
        
        if len(peaks_cnc) > 0:
            plt.figure(figsize=(20,6))
            plt.plot(np.arange(peaks_cnc[0]+freq_cnc)/freq_cnc, signal[:peaks_cnc[0]+freq_cnc], label=label+"_Peak + 1s")
            plt.scatter(peaks_cnc[0]/freq_cnc,signal[peaks_cnc[0]], color = 'hotpink',zorder=10)
            plt.legend(loc='lower left')
            plt.ylim([min(signal[:peaks_cnc[0]+freq_cnc]),max(signal[:peaks_cnc[0]+freq_cnc])])
            plt.show()
        
        secs = input('Was the peak chosen correctly? Y or [N]: ')
        if secs.lower() == 'y':
            length_to_peak = peaks_cnc[0]
            print(f'First peak after {peaks_cnc[0]/float(freq_cnc)}s in position {peaks_cnc[0]}')
            break
        
        secs = input('Input height of first peak of the signal: ')
        if secs != '':
            height=float(secs)
        else:
            height=0
        
    if rpm_avg < 200:
        height_rpm[0]=height
    elif rpm_avg < 400:
        height_rpm[1]=height
    else:
        height_rpm[2]=height
            
    file_peaks['i_freq_peaks'] = freq_cnc
    file_peaks['i_peaks_value_max'] = max_h
    file_peaks['i_peaks_value_min'] = min_h
    file_peaks['i_peaks_value_avg'] = avg_h
    file_peaks['i_peak_height'] = height
    file_peaks['i_peak_first'] = int(peaks_cnc[0])
    file_peaks['i_peak_last'] = int(peaks_cnc[len(peaks_cnc)-1])
    file_peaks['i_peak_qty'] = len(peaks_cnc)
    file_peaks['i_peak_distance'] = int(np.max(peaks_cnc) - np.min(peaks_cnc))
    
    if 'AE_F' in mat.keys():
        print('************************** External signals 50 kHz')
        
        while True:
            secs = input('Choose a signal (Fx, Fy, or [Fz]): ')#' or S to skip')
            if secs.lower() == 'fx' or secs.lower() == 'fy' or secs.lower() == 'fz':
                label='F'+secs.lower()[1]
                break
            elif secs.lower() == 'ax' or secs.lower() == 'ay' or secs.lower() == 'az':
                label='A'+secs.lower()[1]
                break
            elif secs == '':
                label='Fz'
                break
            elif secs.lower() == 's':
                label='skip'
                break
            
        signal=mat[label]
        file_peaks['e1_signal'] = label
                
        file_peaks['e1_start'] = 0
        file_peaks['e1_end'] = len(signal)
        
        cut_size=0
        while True:
            secs = input('Input quantity of seconds to search at the beginning of the signal: ')
            if secs != '':
                cut_size=float(secs)
            else:
                cut_size=0
                
            plt.figure(figsize=(20,6))
            plt.plot(np.arange(int(freq*cut_size))/file_peaks['Hz_F'], signal[:int(freq*cut_size)], label=label+f'_{cut_size}s')
            plt.legend(loc='upper left')
            y_min, y_max = plt.ylim()
            skip = (y_max - y_min) / 10
            
            for y in np.arange(y_min, y_max+skip, skip):
                plt.axhline(y=y, color='lightgrey', linestyle='-', zorder=0)
            plt.show()
            
            secs = input('Search for peaks in the portion of the signal selected? [Y] or N: ')
            if secs.lower() != 'n':
                break
            
        file_peaks['e1_sec_search'] = cut_size

        height_e = 0
        while True:
            freq=file_peaks['Hz_F']
            
            secs = input('Input max height for finding the first peak: ')
            if secs != '':
                height_e=float(secs)
            else:
                height_e=0
                
            print('Qty of peaks in CNC signal:', file_peaks['i_peak_qty'])
                
            peaks_e1, freq, avg_h, max_h, min_h  = sh.calcular_freq(signal, label, height_e, freq, rpm_avg)
            length_before_peak = int(length_to_peak/float(freq_cnc)*float(freq))
            print(f'Section before peak should be at {length_before_peak/float(freq)}s in position {length_before_peak}')
            
            if len(peaks_e1) > 0:
                if peaks_e1[0]-length_before_peak >= 0:
                    file_peaks['e1_start'] = int(peaks_e1[0]-length_before_peak)
                    print('External signal start:',file_peaks['e1_start'])
                else:
                    file_peaks['e1_start'] = 0
                    print('External signal start:',file_peaks['e1_start'])
                    length_to_peak = int(peaks_e1[0]/float(freq)*float(freq_cnc))
                    print(f'Adjusting internal signal start from {file_peaks["i_start"]} to {peaks_cnc[0]-length_to_peak}')
                    file_peaks['i_start'] = int(peaks_cnc[0]-length_to_peak)
                
                file_peaks['e1_end'] = int((file_peaks['i_end']-file_peaks['i_start'])/freq_cnc*freq)+file_peaks['e1_start']
                print(f'Internal signal ends in {file_peaks["i_end"]} and external should end in {file_peaks["e1_end"]}')
                print(f"Length of internal signal: {file_peaks['i_end']-file_peaks['i_start']}")
                print(f"Length of external signal: {file_peaks['e1_end']-file_peaks['e1_start']}")
                print(f"Adjusted length of external signal: {(file_peaks['e1_end']-file_peaks['e1_start'])/freq*freq_cnc}")
                if file_peaks['e1_end']-file_peaks['e1_start'] > len(signal[file_peaks['e1_start']:]):
                    print(f"Adjusting end of internal signal to {int((len(signal)-file_peaks['e1_start'])/float(freq)*float(freq_cnc))+file_peaks['i_start']}")
                    file_peaks['e1_end'] = len(signal)
                    file_peaks['i_end'] = int((file_peaks['e1_end']-file_peaks['e1_start'])/float(freq)*float(freq_cnc))+file_peaks['i_start']
                    print(f"Length of internal signal: {file_peaks['i_end']-file_peaks['i_start']}")
                    print(f"Length of external signal: {file_peaks['e1_end']-file_peaks['e1_start']}")
                    print(f"Adjusted length of external signal: {(file_peaks['e1_end']-file_peaks['e1_start'])/freq*freq_cnc}")
                
                cut_off = file_peaks['e1_start']
                print(f'Cut off section begins in {cut_off} and ends in {peaks_e1[0]}')
                    
                plt.figure(figsize=(20,6))
                plt.plot(np.arange(peaks_e1[0]-cut_off+int(freq))/freq,signal[cut_off:peaks_e1[0]+int(freq)], label=label+"_Peak + 1s")
                plt.scatter((peaks_e1[0]-cut_off)/freq,signal[peaks_e1[0]], color = 'hotpink',zorder=10)
                plt.scatter(0,signal[cut_off], color = 'green',zorder=10)
                plt.legend(loc='upper left')
                plt.show()
                
                sec = 5
                if max(peaks_cnc) > file_peaks['i_end']:
                    peaks_print = sh.drop_after_x(peaks_cnc,file_peaks['i_end'])
                    file_peaks['i_peak_last'] = int(peaks_print[len(peaks_print)-1])
                    file_peaks['i_peak_qty'] = len(peaks_print)
                    file_peaks['i_peak_distance'] = int(np.max(peaks_print) - np.min(peaks_print))
                else:
                    peaks_print = peaks_cnc
                peaks_5s_e1 = sh.drop_after_x(peaks_e1,int(freq*sec+cut_off))
                peaks_cnc_5s = sh.drop_after_x(peaks_cnc,int(freq_cnc*sec+file_peaks['i_start']))
                
                if len(mat['SREAL']) >= int(freq_cnc*sec)+file_peaks['i_start']:
                    fig, axs = plt.subplots(5, 1, figsize=(20,25))
                    axs[0].plot(mat['SREAL'][file_peaks['i_start']:int(freq_cnc*sec)+file_peaks['i_start']]/6000, label='SREAL')
                    axs[0].legend(loc='upper left')
                    axs[0].scatter((peaks_cnc_5s-file_peaks['i_start']),mat['SREAL'][peaks_cnc_5s]/6000, color = 'hotpink',zorder=10)
                    axs[1].plot(mat['TV50'][file_peaks['i_start']:int(freq_cnc*sec)+file_peaks['i_start']], label='TV50')
                    axs[1].legend(loc='upper left')
                    axs[1].scatter((peaks_cnc_5s-file_peaks['i_start']),mat['TV50'][peaks_cnc_5s], color = 'hotpink',zorder=10)
                    axs[2].plot(mat['TV2_Z'][file_peaks['i_start']:int(freq_cnc*sec)+file_peaks['i_start']]/10000, label='TV2_Z')
                    axs[2].legend(loc='upper left')
                    axs[2].scatter((peaks_cnc_5s-file_peaks['i_start']),mat['TV2_Z'][peaks_cnc_5s]/10000, color = 'hotpink',zorder=10)
                                
                    axs[3].plot(mat['Fz'][cut_off:file_peaks['e1_start']+int(freq*sec)], label='Fz')
                    axs[3].legend(loc='upper left')
                    axs[3].scatter((peaks_5s_e1-cut_off),mat['Fz'][peaks_5s_e1], color = 'hotpink',zorder=10)
                    axs[4].plot(mat['Az'][cut_off:file_peaks['e1_start']+int(freq*sec)], label='Az')
                    axs[4].legend(loc='upper left')
                    axs[4].scatter((peaks_5s_e1-cut_off),mat['Az'][peaks_5s_e1], color = 'hotpink',zorder=10)
                    plt.tight_layout()
                    plt.show()
                    
                    peaks_5s_e1 = sh.drop_before_x(peaks_e1,int(file_peaks['e1_end'] - freq*sec))
                    peaks_cnc_5s = sh.drop_before_x(peaks_cnc,int(file_peaks['i_end']-freq_cnc*sec))
                
                    fig, axs = plt.subplots(5, 1, figsize=(20,25))
                    axs[0].plot(mat['SREAL'][file_peaks['i_end']-int(freq_cnc*sec):file_peaks['i_end']]/6000, label='SREAL')
                    axs[0].legend(loc='upper left')
                    axs[0].scatter(peaks_cnc_5s-int(file_peaks['i_end'] - freq*sec),mat['SREAL'][peaks_cnc_5s]/6000, color = 'hotpink',zorder=10)
                    axs[1].plot(mat['TV50'][file_peaks['i_end']-int(freq_cnc*sec):file_peaks['i_end']], label='TV50')
                    axs[1].legend(loc='upper left')
                    axs[1].scatter(peaks_cnc_5s-int(file_peaks['i_end'] - freq*sec),mat['TV50'][peaks_cnc_5s], color = 'hotpink',zorder=10)
                    axs[2].plot(mat['TV2_Z'][file_peaks['i_end']-int(freq_cnc*sec):file_peaks['i_end']]/10000, label='TV2_Z')
                    axs[2].legend(loc='upper left')
                    axs[2].scatter(peaks_cnc_5s-int(file_peaks['i_end'] - freq*sec),mat['TV2_Z'][peaks_cnc_5s]/10000, color = 'hotpink',zorder=10)
                                
                    axs[3].plot(mat['Fz'][file_peaks['e1_end']-int(freq*sec):file_peaks['e1_end']], label='Fz')
                    axs[3].legend(loc='upper left')
                    axs[3].scatter((peaks_5s_e1-int(file_peaks['e1_end'] - freq*sec)),mat['Fz'][peaks_5s_e1], color = 'hotpink',zorder=10)
                    axs[4].plot(mat['Az'][file_peaks['e1_end']-int(freq*sec):file_peaks['e1_end']], label='Az')
                    axs[4].legend(loc='upper left')
                    axs[4].scatter((peaks_5s_e1-int(file_peaks['e1_end'] - freq*sec)),mat['Az'][peaks_5s_e1], color = 'hotpink',zorder=10)
                    plt.tight_layout()
                    plt.show()
                
                fig, axs = plt.subplots(5, 1, figsize=(20,25))
                axs[0].plot(mat['SREAL'][file_peaks['i_start']:file_peaks['i_end']]/6000, label='SREAL')
                axs[0].legend(loc='upper left')
                axs[0].scatter(peaks_print-file_peaks['i_start'],mat['SREAL'][peaks_print]/6000, color = 'hotpink',zorder=10)
                axs[1].plot(mat['TV50'][file_peaks['i_start']:file_peaks['i_end']], label='TV50')
                axs[1].legend(loc='upper left')
                axs[1].scatter(peaks_print-file_peaks['i_start'],mat['TV50'][peaks_print], color = 'hotpink',zorder=10)
                axs[2].plot(mat['TV2_Z'][file_peaks['i_start']:file_peaks['i_end']]/10000, label='TV2_Z')
                axs[2].legend(loc='upper left')
                axs[2].scatter(peaks_print-file_peaks['i_start'],mat['TV2_Z'][peaks_print]/10000, color = 'hotpink',zorder=10)
                
                axs[3].plot(mat['Fz'][cut_off:file_peaks['e1_end']], label='Fz')
                axs[3].legend(loc='upper left')
                axs[3].scatter(peaks_e1-cut_off,mat['Fz'][peaks_e1], color = 'hotpink',zorder=10)
                axs[4].plot(mat['Az'][cut_off:file_peaks['e1_end']], label='Az')
                axs[4].legend(loc='upper left')
                axs[4].scatter(peaks_e1-cut_off,mat['Az'][peaks_e1], color = 'hotpink',zorder=10)
                plt.tight_layout()
                plt.show()
                
                secs = input('Continue with the 1 MHz signals? Y or [N]: ')
                if secs.lower() == 'y':
                    break
                
        file_peaks['e1_freq_peaks'] = freq
        file_peaks['e1_peaks_value_max'] = max_h
        file_peaks['e1_peaks_value_min'] = min_h
        file_peaks['e1_peaks_value_avg'] = avg_h
        file_peaks['e1_peak_height'] = height_e
        file_peaks['e1_peak_first'] = int(peaks_e1[0])
        file_peaks['e1_peak_last'] = int(peaks_e1[len(peaks_e1)-1])
        file_peaks['e1_peak_qty'] = len(peaks_e1)
        file_peaks['e1_peak_distance'] = int(np.max(peaks_e1) - np.min(peaks_e1))    
        
        print('************************** External signals 1 MHz')
        
        label='AE_RMS'
        freq=file_peaks['Hz_AE']
        signal=mat[label]
        file_peaks['e2_signal'] = label
                
        file_peaks['e2_start'] = 0
        file_peaks['e2_end'] = len(signal)
        
        cut_size=0
        while True:
            secs = input('Input quantity of seconds to search at the beginning of the signal: ')
            if secs != '':
                cut_size=float(secs)
            else:
                cut_size=0
                
            plt.figure(figsize=(20,6))
            plt.plot(np.arange(int(freq*cut_size))/file_peaks['Hz_AE'], signal[:int(freq*cut_size)], label=label+f'_{cut_size}s')
            plt.legend(loc='upper left')
            y_min, y_max = plt.ylim()
            skip = (y_max - y_min) / 10
            
            for y in np.arange(y_min, y_max+skip, skip):
                plt.axhline(y=y, color='lightgrey', linestyle='-', zorder=0)
            plt.show()
            
            secs = input('Search for peaks in the portion of the signal selected? [Y] or N: ')
            if secs.lower() != 'n':
                break
            
        file_peaks['e2_sec_search'] = cut_size
            
        
        height_e = 0
        while True:
            freq=file_peaks['Hz_AE']
            
            secs = input('Input max height for finding the first peak: ')
            if secs != '':
                height_e=float(secs)
            else:
                height_e=0
                
            print('Qty of peaks in CNC signal:', file_peaks['i_peak_qty'])
                
            peaks_e2, freq, avg_h, max_h, min_h  = sh.calcular_freq(signal, label, height_e, freq, rpm_avg)        
            length_before_peak = int(length_to_peak/float(freq_cnc)*float(freq))
            print(f'Section before peak should be at {length_before_peak/float(freq)}s in position {length_before_peak}')
            
            if len(peaks_e2) > 0:
                if peaks_e2[0]-length_before_peak >= 0:
                    file_peaks['e2_start'] = int(peaks_e2[0]-length_before_peak)
                    print('External signal start:',file_peaks['e2_start'])
                    
                file_peaks['e2_end'] = int((file_peaks['i_end']-file_peaks['i_start'])/freq_cnc*freq)+file_peaks['e2_start']
                if max(peaks_e2) > file_peaks['e2_end']:
                    peaks_e2 = sh.drop_after_x(peaks_e2,file_peaks['e2_end'])
                print(f'Internal signal ends in {file_peaks["i_end"]} and external should end in {file_peaks["e2_end"]}')
                print(f"Length of internal signal: {file_peaks['i_end']-file_peaks['i_start']}")
                print(f"Length of external signal: {file_peaks['e2_end']-file_peaks['e2_start']}")
                print(f"Adjusted length of external signal: {(file_peaks['e2_end']-file_peaks['e2_start'])/freq*freq_cnc}")
                if file_peaks['e2_end']-file_peaks['e2_start'] > len(signal[file_peaks['e2_start']:]):
                    print(f"Adjusting end of internal signal to {int((len(signal)-file_peaks['e2_start'])/float(freq)*float(freq_cnc))+file_peaks['i_start']}")
                    file_peaks['e2_end'] = len(signal)
                    file_peaks['i_end'] = int((file_peaks['e2_end']-file_peaks['e2_start'])/float(freq)*float(freq_cnc))+file_peaks['i_start']
                    file_peaks['e1_end'] = int((file_peaks['e2_end']-file_peaks['e2_start'])/float(freq)*file_peaks['e1_freq_peaks'])+file_peaks['e1_start']
                    print(f"Length of internal signal: {file_peaks['i_end']-file_peaks['i_start']}")
                    print(f"Length of external signal: {file_peaks['e2_end']-file_peaks['e2_start']}")
                    print(f"Adjusted length of external signal: {(file_peaks['e2_end']-file_peaks['e2_start'])/freq*freq_cnc}")
                
                cut_off = file_peaks['e2_start']
                print(f'Cut off section begins in {cut_off} and ends in {peaks_e2[0]}')
                
                plt.figure(figsize=(20,6))
                plt.plot(np.arange(peaks_e2[0]-cut_off+int(freq))/freq,signal[cut_off:peaks_e2[0]+int(freq)], label=label+"_Peak + 1s")
                plt.scatter((peaks_e2[0]-cut_off)/freq,signal[peaks_e2[0]], color = 'hotpink',zorder=10)
                plt.scatter(0,signal[cut_off], color = 'green',zorder=10)
                plt.legend(loc='upper left')
                plt.show()
            
                sec = 5
                if max(peaks_cnc) > file_peaks['i_end']:
                    peaks_print = sh.drop_after_x(peaks_cnc,file_peaks['i_end'])
                    file_peaks['i_peak_last'] = int(peaks_print[len(peaks_print)-1])
                    file_peaks['i_peak_qty'] = len(peaks_print)
                    file_peaks['i_peak_distance'] = int(np.max(peaks_print) - np.min(peaks_print))
                else:
                    peaks_print = peaks_cnc
                if max(peaks_e1) > file_peaks['e1_end']:
                    peaks_e1_print = sh.drop_after_x(peaks_e1,file_peaks['e1_end'])
                    file_peaks['e1_peak_last'] = int(peaks_e1_print[len(peaks_e1_print)-1])
                    file_peaks['e1_peak_qty'] = len(peaks_e1_print)
                    file_peaks['e1_peak_distance'] = int(np.max(peaks_e1_print) - np.min(peaks_e1_print))    
                else:
                    peaks_e1_print = peaks_e1
                peaks_5s_e1 = sh.drop_after_x(peaks_e1,int(file_peaks['e1_freq_peaks']*sec+file_peaks['e1_start']))
                peaks_5s_e2 = sh.drop_after_x(peaks_e2,int(freq*sec+cut_off))
                peaks_cnc_5s = sh.drop_after_x(peaks_cnc,int(freq_cnc*sec+file_peaks['i_start']))
                
                if len(mat['SREAL']) >= int(freq_cnc*sec)+file_peaks['i_start']:
                    fig, axs = plt.subplots(6, 1, figsize=(20,30))
                    axs[0].plot(mat['SREAL'][file_peaks['i_start']:int(freq_cnc*sec)+file_peaks['i_start']]/6000, label='SREAL')
                    axs[0].legend(loc='upper left')
                    axs[0].scatter((peaks_cnc_5s-file_peaks['i_start']),mat['SREAL'][peaks_cnc_5s]/6000, color = 'hotpink',zorder=10)
                    axs[1].plot(mat['TV50'][file_peaks['i_start']:int(freq_cnc*sec)+file_peaks['i_start']], label='TV50')
                    axs[1].legend(loc='upper left')
                    axs[1].scatter((peaks_cnc_5s-file_peaks['i_start']),mat['TV50'][peaks_cnc_5s], color = 'hotpink',zorder=10)
                    axs[2].plot(mat['TV2_Z'][file_peaks['i_start']:int(freq_cnc*sec)+file_peaks['i_start']]/10000, label='TV2_Z')
                    axs[2].legend(loc='upper left')
                    axs[2].scatter((peaks_cnc_5s-file_peaks['i_start']),mat['TV2_Z'][peaks_cnc_5s]/10000, color = 'hotpink',zorder=10)
                                
                    axs[3].plot(mat['Fz'][file_peaks['e1_start']:file_peaks['e1_start']+int(file_peaks['e1_freq_peaks']*sec)], label='Fz')
                    axs[3].legend(loc='upper left')
                    axs[3].scatter((peaks_5s_e1-file_peaks['e1_start']),mat['Fz'][peaks_5s_e1], color = 'hotpink',zorder=10)
                    axs[4].plot(mat['Az'][file_peaks['e1_start']:file_peaks['e1_start']+int(file_peaks['e1_freq_peaks']*sec)], label='Az')
                    axs[4].legend(loc='upper left')
                    axs[4].scatter((peaks_5s_e1-file_peaks['e1_start']),mat['Az'][peaks_5s_e1], color = 'hotpink',zorder=10)
                    
                    axs[5].plot(mat['AE_RMS'][cut_off:file_peaks['e2_start']+int(freq*sec)], label='AE_RMS')
                    axs[5].legend(loc='upper left')
                    axs[5].scatter(peaks_5s_e2-cut_off,mat['AE_RMS'][peaks_5s_e2], color = 'hotpink',zorder=10)
                    plt.tight_layout()
                    plt.show()
                
                fig, axs = plt.subplots(6, 1, figsize=(20,30))
                axs[0].plot(mat['SREAL'][file_peaks['i_start']:file_peaks['i_end']]/6000, label='SREAL')
                axs[0].legend(loc='upper left')
                axs[0].scatter(peaks_print-file_peaks['i_start'],mat['SREAL'][peaks_print]/6000, color = 'hotpink',zorder=10)
                axs[1].plot(mat['TV50'][file_peaks['i_start']:file_peaks['i_end']], label='TV50')
                axs[1].legend(loc='upper left')
                axs[1].scatter(peaks_print-file_peaks['i_start'],mat['TV50'][peaks_print], color = 'hotpink',zorder=10)
                axs[2].plot(mat['TV2_Z'][file_peaks['i_start']:file_peaks['i_end']]/10000, label='TV2_Z')
                axs[2].legend(loc='upper left')
                axs[2].scatter(peaks_print-file_peaks['i_start'],mat['TV2_Z'][peaks_print]/10000, color = 'hotpink',zorder=10)
                
                axs[3].plot(mat['Fz'][file_peaks['e1_start']:file_peaks['e1_end']], label='Fz')
                axs[3].legend(loc='upper left')
                axs[3].scatter(peaks_e1_print-file_peaks['e1_start'],mat['Fz'][peaks_e1_print], color = 'hotpink',zorder=10)
                axs[4].plot(mat['Az'][file_peaks['e1_start']:file_peaks['e1_end']], label='Az')
                axs[4].legend(loc='upper left')
                axs[4].scatter(peaks_e1_print-file_peaks['e1_start'],mat['Az'][peaks_e1_print], color = 'hotpink',zorder=10)
                
                axs[5].plot(mat['AE_RMS'][cut_off:file_peaks['e2_end']], label='AE_RMS')
                axs[5].legend(loc='upper left')
                axs[5].scatter(peaks_e2-cut_off,mat['AE_RMS'][peaks_e2], color = 'hotpink',zorder=10)
                plt.tight_layout()
                plt.show()
                
                secs = input('Apply cuts to the signals? Y or [N]: ')
                if secs.lower() == 'y':
                    break
    
        file_peaks['e2_freq_peaks'] = freq
        file_peaks['e2_peaks_value_max'] = max_h
        file_peaks['e2_peaks_value_min'] = min_h
        file_peaks['e2_peaks_value_avg'] = avg_h
        file_peaks['e2_peak_height'] = height_e
        file_peaks['e2_peak_first'] = int(peaks_e2[0])
        file_peaks['e2_peak_last'] = int(peaks_e2[len(peaks_e2)-1])
        file_peaks['e2_peak_qty'] = len(peaks_e2)
        file_peaks['e2_peak_distance'] = int(np.max(peaks_e2) - np.min(peaks_e2))    
        
        file_peaks['i_freq_calc'] = file_peaks['i_peak_distance'] * freq / file_peaks['e2_peak_distance']
    
    secs = input('Flag signal? Y or [N]: ')
    if secs.lower() == 'y':
        file_peaks['flagged'] = True
    
    mat['POS_X'] = mat['POS_X'][file_peaks['i_start']:file_peaks['i_end']]
    mat['POS_Y'] = mat['POS_Y'][file_peaks['i_start']:file_peaks['i_end']]
    mat['POS_Z'] = mat['POS_Z'][file_peaks['i_start']:file_peaks['i_end']]
    mat['POS_S'] = mat['POS_S'][file_peaks['i_start']:file_peaks['i_end']]
    mat['SREAL'] = mat['SREAL'][file_peaks['i_start']:file_peaks['i_end']]
    mat['CV3_S'] = mat['CV3_S'][file_peaks['i_start']:file_peaks['i_end']]
    mat['CV3_X'] = mat['CV3_X'][file_peaks['i_start']:file_peaks['i_end']]
    mat['CV3_Y'] = mat['CV3_Y'][file_peaks['i_start']:file_peaks['i_end']]
    mat['CV3_Z'] = mat['CV3_Z'][file_peaks['i_start']:file_peaks['i_end']]
    mat['TV2_S'] = mat['TV2_S'][file_peaks['i_start']:file_peaks['i_end']]
    mat['TV2_X'] = mat['TV2_X'][file_peaks['i_start']:file_peaks['i_end']]
    mat['TV2_Y'] = mat['TV2_Y'][file_peaks['i_start']:file_peaks['i_end']]
    mat['TV2_Z'] = mat['TV2_Z'][file_peaks['i_start']:file_peaks['i_end']]
    mat['TV50'] = mat['TV50'][file_peaks['i_start']:file_peaks['i_end']]
    mat['TV51'] = mat['TV51'][file_peaks['i_start']:file_peaks['i_end']]
    mat['FREAL'] = mat['FREAL'][file_peaks['i_start']:file_peaks['i_end']]
    
    if 'AE_F' in mat.keys():
        mat['Ax'] = mat['Ax'][file_peaks['e1_start']:file_peaks['e1_end']]
        mat['Ay'] = mat['Ay'][file_peaks['e1_start']:file_peaks['e1_end']]
        mat['Az'] = mat['Az'][file_peaks['e1_start']:file_peaks['e1_end']]
        mat['Fx'] = mat['Fx'][file_peaks['e1_start']:file_peaks['e1_end']]
        mat['Fy'] = mat['Fy'][file_peaks['e1_start']:file_peaks['e1_end']]
        mat['Fz'] = mat['Fz'][file_peaks['e1_start']:file_peaks['e1_end']]
        
        mat['AE_RMS'] = mat['AE_RMS'][file_peaks['e2_start']:file_peaks['e2_end']]
        mat['AE_F'] = mat['AE_F'][file_peaks['e2_start']:file_peaks['e2_end']]
    
    scipy.io.savemat(output, mat)
    
    print(file_peaks)
    pre_sync.append(file_peaks)
        
    with open(json_file, "w") as f:
        json.dump(file_peaks, f, indent=4)
    
print(pre_sync)

df = pd.DataFrame(pre_sync)
df.to_csv('signals_pre_sync.csv',sep=';',decimal='.')

with open("signals_pre_sync.json", "w") as f:
    json.dump(pre_sync, f, indent=4)
