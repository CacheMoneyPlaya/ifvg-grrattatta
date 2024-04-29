import json
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from scipy.signal import find_peaks
import datetime
import numpy as np
import requests
import warnings
warnings.filterwarnings("ignore")

number_of_liquidity_points_to_save_per_side = 2

def fetch_binance_data(symbol, interval, limit=1500, end_time=None):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    if end_time:
        url += f"&endTime={end_time}"
    data = requests.get(url).json()
    return data

def fetch_multiple_data(symbol, interval, limit=1500, num_sets=3):
    data_sets = []
    for _ in range(num_sets):
        if data_sets:
            end_time = data_sets[-1][-1][0] - (int(interval[:-1]) * limit * 60000)
        else:
            end_time = None
        data = fetch_binance_data(symbol, interval, limit, end_time)
        data_sets.append(data)
    return data_sets


def get_nearest_liq_levels():
    symbol = "BTCUSDT"
    interval = "5m"
    num_sets = 4
    data_sets = fetch_multiple_data(symbol, interval, num_sets=num_sets)

    combined_data = []
    for data in data_sets:
        combined_data.extend(data)

    combined_data.sort(key=lambda x: x[0])

    candlesticks = [{"timestamp": c[0] / 1000, "open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4])} for c in combined_data]
    df = pd.DataFrame(candlesticks).set_index(pd.to_datetime(pd.DataFrame(candlesticks)['timestamp'], unit='s'))

    h = df['high'].values
    l = df['low'].values
    th = 20.0
    distance = 20
    pks, _ = find_peaks(h, prominence=th, distance=distance)
    vlys, _ = find_peaks(-l, prominence=th, distance=distance)

    filtered_pks = []
    for pk in pks:
        future_prices = h[pk+1:]
        if not np.any(future_prices > h[pk]) and pk <= len(df) - 25:
            filtered_pks.append(pk)

    filtered_vlys = []
    for vly in vlys:
        future_prices = l[vly+1:]
        if not np.any(future_prices < l[vly]) and vly <= len(df) - 25:
            filtered_vlys.append(vly)

    filtered_pks.reverse()
    filtered_vlys.reverse()

    return {
        "BSL": [{"price": df['high'].iloc[pk]} for pk in filtered_pks[:number_of_liquidity_points_to_save_per_side]],
        "SSL": [{"price": df['low'].iloc[vly]} for vly in filtered_vlys[:number_of_liquidity_points_to_save_per_side]]
    }
