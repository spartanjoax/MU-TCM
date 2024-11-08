# -*- coding: utf-8 -*-
"""
Copyright (C) 2024, José Joaquín Peralta Abadía / Mondragon Unibertsitatea
This program is free software: you can redistribute it and/or modify it under the terms of
the GNU Affero General Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this
program. If not, see <https://www.gnu.org/licenses/>.

DISCLAIMER:
This software is provided "as-is" without any express or implied warranties, including but
not limited to any implied warranties of merchantability, fitness for a particular purpose,
or non-infringement. The authors are not liable for any damages or issues that arise from
using, modifying, or distributing this software.
"""

import os
import signal_helper as sh
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import ntpath
from scipy.stats import kurtosis, skew
import argparse

def extract_features(input_dir):
    """
    Performs feature extraction on the synchronised signals, generating time, frequency, and 
    time-frequency-domain features (e.g., RMS, kurtosis, peak-to-peak, wavelet energy) that 
    can be used for TCM.

    Args:
        input_dir (str): Path to the directory containing the synchronised signal data.
    """

    # Ensure the input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: The input directory '{input_dir}' does not exist.")
        return

    print('====================================================')
    print(f"Extracting features from '{input_dir}'...")

    mother_wavelet = 'db8'
    wavelet_level = 10

    pre_sync = []

    x_tick_qty = 40
    y_tick_qty = 10

    files = sh.get_file_list(root=input_dir, pattern='*.mat')
    print(f'File quantity: {len(files)}')

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
        print(f'Analyzing file: {file}')
        
        mat, rpm_avg = sh.load_and_plot_file(file,freq_i=1,freq_e=1)
        file = ntpath.basename(file)
            
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
    df.to_csv(input_dir + '/signals_stats.csv',sep=';',decimal='.')

    print('====================================================')
    print("Feature extraction completed.")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Extract time, frequency, and time-frequency-domain features from synchronised signals.")
    parser.add_argument('--input_dir', 
        default="../signals_synced",
        help="Path to the directory containing synchronized data.")

    # Parse arguments
    args = parser.parse_args()

    # Run the extraction function with the provided argument
    extract_features(args.input_dir)