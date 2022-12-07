#! python
import os
import shutil
import glob
from tqdm import tqdm
from pathlib import Path
import random
from distutils.dir_util import copy_tree

import pandas as pd
import matplotlib.pyplot as plt

import numpy as np

from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox
from scipy.stats import kurtosis

from model.conf import RESULT_DIR, N_STEPS, N_RUNS, SEED
from model.stats import *

plt.style.use('ggplot')

latest = Path('results/latest').absolute()
if latest.is_dir():
    shutil.rmtree(latest)
latest.mkdir(exist_ok=True, parents=True)


n_run = len(glob.glob(f'{RESULT_DIR}/run_*'))
while os.path.isdir(f'{RESULT_DIR}/run_{n_run}'):
    n_run += 1
run_dir = f'{RESULT_DIR}/run_{n_run}'
Path(run_dir).mkdir(parents=True)
os.chdir(run_dir)


GUI = False
DIRECT_SAVE = True

if GUI:
    print('SERVER STARTING')
    from model.server import server

    server.launch()

    print('SERVER STOPPED')

else:
    from model.Market import Mercato, datacollector_dict

    print("Launching without GUI")
    print(f"Saving results in {run_dir}")

    import model.conf
    shutil.copyfile(model.conf.__file__, f'conf.py')
    os.mkdir(f'immagini')

    model_vars_df = pd.DataFrame(columns=list(datacollector_dict['model_reporters'].keys()))
    # agent_vars_dataframe = pd.DataFrame(columns=list(datacollector_dict['agent_reporters'].keys()) + ['step', 'run'])
    model_vars_df.index = pd.MultiIndex.from_arrays([[],[]], names=['run', 'step'])
    # agent_vars_dataframe.set_index(['run', 'step'])
    kurtosis_windows = (10, 60, 600)
    stats_df = pd.DataFrame(columns=['seed', 'adfuller', 'acorr_ljungbox', *(f'kurtosis{w}' for w in kurtosis_windows)])
    stats_df.index.name = 'run'

    random.seed(SEED)
    seeds = [random.randint(0, 1000) for _ in range(N_RUNS)]

    for n_run, seed in enumerate(seeds):
        random.seed(seed)
        np.random.seed(seed)
        print("============")
        print(f"RUN = {n_run}")
        print(f"SEED = {seed}")
        print("============")
        model = Mercato()

        model.start()
        for i in tqdm(range(N_STEPS)):
            model.step()

        df = model.datacollector.get_model_vars_dataframe()
        df['run'] = n_run
        df.index.name = 'step'
        df.to_csv(f"model_vars.csv", mode='a', header=n_run==0)
        print("Data collected")

        if DIRECT_SAVE:
            print('Saving plots...')

            adf_pvalue = adfuller_test(df)      
            volclus_pvalue = volclus_test(df)
            kurtosis_pvalues = kurtosis_test(df, kurtosis_windows)

            fig , ax = plt.subplots(3,1, figsize=(20, 16),dpi=300)
            
            ax[0].set_title(f'Price time series')
            ax[0].set_xlabel('Step')
            ax[0].set_ylabel('Price')
            ax[0].plot(df.price, label=f'Run {i}')
            
            ax[1].set_title(f'Technical fraction time series')
            ax[1].set_xlabel('Step')
            ax[1].set_ylabel('Technical fraction')
            ax[1].plot(df.technical_fraction, label=f'Run {i}')

            ax[2].set_title(f'Opinion Index time series')
            ax[2].set_xlabel('Step')
            ax[2].set_ylabel('Opinion Index')
            ax[2].plot(df.opinion_index, label = f'Run {i}')
            
            stats_df.loc[n_run] = [seed, adf_pvalue, volclus_pvalue, *kurtosis_pvalues]
            stats_df.to_csv('stats.csv')
            title = f'DF-Test pvalue = {adf_pvalue:.3f} \u21FE Unit Root: {adf_pvalue>0.05}\n' +\
                    f'VC-Test pvalue = {volclus_pvalue:.3f} \u21FE Volatility Clustering:{volclus_pvalue<0.05} \n' +\
                    ''.join(
                        (f'Kurtosis {w} = {v:.3f} \u21FE Leptokurtic: {v>0}\n' for w, v in zip(kurtosis_windows, kurtosis_pvalues))
                    )
                    #'Kurtosis minute = ', kurtosisvalues[1].round(3),' \u21FE ','Leptokurtic:', kurtosisvalues[0]>0,'\n'
                    #'Kurtosis hour = ', kurtosisvalues[2].round(3),' \u21FE ','Leptokurtic:', kurtosisvalues[0]>0,'\n'    ]
            fig.suptitle(title,fontsize=20,color='black')
            plt.tight_layout()
            fig.savefig(f'immagini/Plots run={n_run}.png',facecolor='white', transparent=False)
            plt.close(fig)

            copy_tree('.', latest.as_posix())
            print("Data printed")
    print('All done')
