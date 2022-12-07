from typing import Iterable

import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox
from scipy.stats import kurtosis

def adfuller_test(df: pd.DataFrame) -> float:
    return adfuller(df.price)[1]

def volclus_test(df: pd.DataFrame, lags=20) -> float:
    volclus = acorr_ljungbox(df.price.to_numpy() ** 2, lags=lags, return_df = True)
    return volclus['lb_pvalue'].min()

def kurtosis_test(df: pd.DataFrame, windows: Iterable[int]) -> list[float]:
    kurtosisvalues = [
        kurtosis(df.price.diff(1).rolling(window).mean().dropna())
        for window in windows
    ]
    return kurtosisvalues

def volclus_test_full_df(df:pd.DataFrame, lags=20) -> pd.DataFrame:
    return pd.DataFrame({
        'square': acorr_ljungbox(df.price ** 2, lags=lags, return_df = True).lb_pvalue.rename('square'),
        'abs': acorr_ljungbox(df.price.apply(abs), lags=lags, return_df = True).lb_pvalue.rename('abs'),
        'normal': acorr_ljungbox(df.price, lags=lags, return_df = True).lb_pvalue.rename('normal')
    })

    
