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

import matplotlib.pyplot as plt
import seaborn as sns
import argparse

from scipy.stats import pearsonr, spearmanr

import pandas as pd
import numpy as np

sns.set_context("paper")
sns.set(font_scale = 1)
#bgcolor='#EAEAF0'
bgcolor=''
color=['hls','Plasma']


def analyse_signals(features_path):
    """
    Evaluates the extracted features against tool wear annotations, providing insights into which 
    features show strong correlations with tool wear, and is useful for understanding the most 
    relevant metrics for TCM.

    Args:
        features_path (str): Path to the file containing the extracted features.
    """

    # Ensure the input directory exists
    if not os.path.exists(features_path):
        print(f"Error: The input file '{features_path}' does not exist.")
        return

    print('====================================================')
    print(f"Analysing features from '{features_path}'...")

    sampling_rate = 250
    mother_wavelet = 'db8'
    wavelet_level = 10

    material_list = ['CastIron.GG30','StainlessSteel.316L']
    signal_list = ['CV3_X','CV3_Y','CV3_Z','TV2_S','TV2_X','TV2_Y',
                'TV2_Z','TV50','TV51','AE_F','AE_RMS','Ax','Ay','Az','Fx','Fy','Fz']
    stat_list = ['rms','var','max','kurt','skew','ptp','speckurt','specskew','wavenergy']
    data_list = [d+'_'+s for d in signal_list for s in stat_list]

    data_file = pd.read_csv(features_path, sep=';',decimal='.', index_col=0)
    data_file['InsertEdge'] = [x.split('_')[0] for x in data_file['_file_name']]
    data_file["Conditions"] = "Vc: " + data_file["Vc"].astype(str) + " - fz: " + data_file["fz"].astype(str)
    data_file["VB_rounded"] = round(data_file["VB"] / 0.1) * 0.1

    print('************************** Experiments per insert and edge:')
    print(data_file[['InsertEdge']].sort_values(by=['InsertEdge']).value_counts().reset_index())

    print('\n************************** Generating plots for comparison between conditions by stats and VB:')
    colors_palette = [['#db5f57', '#a157db', '#4EA6DC', '#88218B','#E32D91','#029676']]
    markers = ['o', 'v', 'p', 's', '^', 'X']
    sns.set(font_scale=1.5, rc={'text.usetex' : False, 'lines.linewidth': 0.7}, style='whitegrid')

    for material in material_list:
        for signal in signal_list:
            print(signal)
            fig, axs = plt.subplots(3, 3, figsize=(20,15))
            counter = 0
            for stat in stat_list:
                variable = signal+'_'+stat
                print(variable)
                row = int(counter / 3)
                column = int(counter % 3)
                ax = axs[row, column]
                
                df_vb_group = data_file[data_file["material"]==material].melt(id_vars=['Conditions','VB']).sort_values(by=['Conditions', 'VB','value'])
                df_vb_group = df_vb_group[df_vb_group.variable == variable].drop(columns=['variable']).reset_index(drop=True)
                df_vb_group['value'] = df_vb_group['value'].astype(float)
                
                if len(df_vb_group) > 0:
                    # Create a loop to iterate through each condition and VB pair
                    j = 0
                    for condition, g in df_vb_group.groupby(['Conditions']):
                        for vb, g in g.groupby(['VB']):
                            x = g['VB'].to_numpy()
                            y = g['value'].to_numpy()
                            
                            # Connect each point to its nearest neighbor with a whisker
                            if len(x) > 1:
                                for i in range(len(x) - 1):
                                    if i == 0:
                                        ax.plot([x[i]], [y[i]], marker='_', markersize=20, color=colors_palette[0][j])
                                    else:
                                        ax.plot([x[i]], [y[i]], marker=markers[j], markersize=5, color=colors_palette[0][j])
                                    ax.plot([x[i], x[i]], [y[i], y[i+1]], linestyle='-',linewidth=1.5, color=colors_palette[0][j])
                                ax.plot([x[len(x)-1]], [y[len(x)-1]], marker='_', markersize=20, color=colors_palette[0][j])
                            else:
                                ax.plot([x[0]], [y[0]], marker=markers[j], markersize=5, color=colors_palette[0][j])
                        j += 1
                    
                    j = 0
                    for condition in np.unique(df_vb_group['Conditions']):
                        mean = df_vb_group[df_vb_group['Conditions'] == condition][['VB','value']].groupby(['VB']).mean()
                        ax.plot(mean.index, mean['value'].values, marker=markers[j], linestyle='-', color=colors_palette[0][j], linewidth=2,label=condition)
                        j += 1
                    
                    ax.set_xlabel('Desgaste de la herramienta, VB (mm)')
                    ax.set_ylabel(variable)
                    if row == 1 and column == 2:
                        ax.legend(loc='right', title='Condiciones', bbox_to_anchor=(1.8, 0.5))
                counter += 1    
                    
            plt.tight_layout()
            plt.savefig(f'Images/vb_curve_plot_{signal}_{material}.png') 
            plt.show()

    print('\n************************** Generating plots for comparison between materials by stats and VB:')
    colors_palette = [['#db5f57', '#a157db', '#4EA6DC', '#88218B','#E32D91','#029676']]
    markers = ['o', 'v', 'p', 's', '^', 'X']
    sns.set(font_scale=1.5, rc={'text.usetex' : False, 'lines.linewidth': 0.7}, style='whitegrid')

    for signal in signal_list:
        print(signal)
        fig, axs = plt.subplots(3, 3, figsize=(20,15))
        counter = 0
        for stat in stat_list:
            variable = signal+'_'+stat
            print(variable)
            #x = 'i_DRV_TV2_X_max'
            row = int(counter / 3)
            column = int(counter % 3)
            ax = axs[row, column]
            
            df_vb_group = data_file[data_file["Conditions"]=='Vc: 100 - fz: 0.1'].melt(id_vars=['material','VB']).sort_values(by=['material', 'VB','value'])
            df_vb_group = df_vb_group[df_vb_group.variable == variable].drop(columns=['variable']).reset_index(drop=True)
            df_vb_group['value'] = df_vb_group['value'].astype(float)
            
            if len(df_vb_group) > 0:
                # Create a loop to iterate through each condition and VB pair
                j = 0
                for condition, g in df_vb_group.groupby(['material']):
                    for vb, g in g.groupby(['VB']):
                        x = g['VB'].to_numpy()
                        y = g['value'].to_numpy()
                        
                        # Connect each point to its nearest neighbor with a whisker
                        if len(x) > 1:
                            for i in range(len(x) - 1):
                                if i == 0:
                                    ax.plot([x[i]], [y[i]], marker='_', markersize=20, color=colors_palette[0][j])
                                else:
                                    ax.plot([x[i]], [y[i]], marker=markers[j], markersize=5, color=colors_palette[0][j])
                                ax.plot([x[i], x[i]], [y[i], y[i+1]], linestyle='-',linewidth=1.5, color=colors_palette[0][j])
                            ax.plot([x[len(x)-1]], [y[len(x)-1]], marker='_', markersize=20, color=colors_palette[0][j])
                        else:
                            ax.plot([x[0]], [y[0]], marker=markers[j], markersize=5, color=colors_palette[0][j])
                    
                        # Plot the points with different colors and markers
                        #ax.scatter(x, y, c=colors_palette[0][j], marker=markers[j], alpha=0.7, s=50)
                    j += 1
                
                # Add mean line by condition
                j = 0
                for condition in np.unique(df_vb_group['material']):
                    mean = df_vb_group[df_vb_group['material'] == condition][['VB','value']].groupby(['VB']).mean()
                    ax.plot(mean.index, mean['value'].values, marker=markers[j], linestyle='-', color=colors_palette[0][j], linewidth=2,label=condition)
                    j += 1
                
                # Set labels and title
                ax.set_xlabel('Desgaste de la herramienta, VB (mm)')
                ax.set_ylabel(variable)
                if row == 1 and column == 2:
                    ax.legend(loc='right', title='materiales', bbox_to_anchor=(1.8, 0.5))
            counter += 1    
                
        # Set legend and display plot
        plt.tight_layout()
        plt.savefig(f'Images/vb_curve_plot_{signal}_compare_vc100_fz01.png') 
        plt.show()
        
    print('\n************************** Calculating Pearson and Spearman coefficients:')
    pearson = []
    spearman = []
    for material in material_list:
        df_vb_group = data_file[data_file["material"]==material]
        if len(df_vb_group) > 0:
            for signal in signal_list:             
                pear_corr = {
                    "stat" : 'pearson',
                    "material" : material,
                    "Signal" : signal,
                    "Condition" : '',
                }
                spear_corr = {
                    "stat" : 'spearman',
                    "material" : material,
                    "Signal" : signal,
                    "Condition" : '',
                }
                for stat in stat_list:
                    variable = signal+'_'+stat
                    g_stat = df_vb_group.dropna(subset=[variable])
                    
                    x = g_stat['VB'].to_numpy()
                    y = g_stat[variable].to_numpy()
                    
                    res = pearsonr(x, y)
                    pear_corr[stat] = res.statistic
                    
                    res = spearmanr(x, y)
                    spear_corr[stat] = res.statistic

                pearson.append(pear_corr)
                spearman.append(spear_corr)
                
                for condition, g in df_vb_group.groupby(['Conditions']):                
                    pear_corr = {
                        "stat" : 'pearson',
                        "material" : material,
                        "Signal" : signal,
                        "Condition" : condition[0],
                    }
                    spear_corr = {
                        "stat" : 'spearman',
                        "material" : material,
                        "Signal" : signal,
                        "Condition" : condition[0],
                    }
                    for stat in stat_list:
                        variable = signal+'_'+stat
                        g_stat = g.dropna(subset=[variable])
                        
                        x = g_stat['VB'].to_numpy()
                        y = g_stat[variable].to_numpy()
                        
                        res = pearsonr(x, y)
                        pear_corr[stat] = res.statistic
                        
                        res = spearmanr(x, y)
                        spear_corr[stat] = res.statistic
        
                    pearson.append(pear_corr)
                    spearman.append(spear_corr)
                    
    input_dir = ntpath.split(features_path)[0]
    df_pears = pd.DataFrame(pearson)
    df_pears['stat'] = 'Pearson'
    df_pears.to_csv(input_dir + '/signal_stats_pearson.csv',sep=';',decimal='.')
    df_spear = pd.DataFrame(spearman)
    df_spear['stat'] = 'Spearman'
    df_spear.to_csv(input_dir + '/signal_stats_spearman.csv',sep=';',decimal='.')
    df = pd.concat([df_pears, df_spear])
    df.to_csv(input_dir + '/signal_stats_combined.csv',sep=';',decimal='.')

    print('====================================================')
    print("Signal evaluation completed.")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Evaluates the extracted features against tool wear annotations.")
    parser.add_argument('--features_path', 
        default="../signals_synced/signals_stats.csv",
        help="Path to the file containing the extracted features.")

    # Parse arguments
    args = parser.parse_args()

    # Run the analysis function with the provided argument
    analyse_signals(args.features_path)