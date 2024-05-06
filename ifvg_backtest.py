import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json
from tqdm import tqdm
from LiquidityLevels.liquidity_levels import get_nearest_liq_levels
from backtest_results import calculate_trade_stats

def gap_valid(num1, num2):
    threshold = 80
    num1 = float(num1)
    num2 = float(num2)

    spread = abs(num1 - num2)

    return spread >= threshold

def determine_fvg(previous, current, next):
        if (
            (previous['high'] >= current['open'] and (previous['high'] <= current['close'])) and
            (next['low'] <= current['close'] and next['low'] >= current['open']) and
            previous['high'] <= next['low'] and gap_valid(next['low'], previous['high'])
        ):
            BULL_FVGS.append({
                'time': current['time'],
                'fvg_high': next['low'],
                'fvg_low': previous['high'],
            })
        elif (
                (previous['low'] <= current['open'] and previous['low'] >= current['close']) and
                (next['high'] >= current['close'] and next['high'] <= current['open']) and
                previous['low'] >= next['high'] and gap_valid(previous['low'], next['high'])
        ):
            BEAR_FVGS.append({
                'time': current['time'],
                'fvg_high': previous['low'],
                'fvg_low': next['high'],
            })

def calculate_full_window_fvg(df):
    for i in range(1, len(df) - 2):
        previous = df.iloc[i - 1]
        current = df.iloc[i]
        next = df.iloc[i + 1]
        determine_fvg(previous, current, next)

    i=0
    while i < len(BEAR_FVGS):
        fvg_time = BEAR_FVGS[i]['time']
        df_after_fvg = df[df['time'] > fvg_time].iloc[:-2]
        if (df_after_fvg['close'] > BEAR_FVGS[i]['fvg_high']).any():
            del BEAR_FVGS[i]
        else:
            i += 1

    i=0
    while i < len(BULL_FVGS):
        fvg_time = BULL_FVGS[i]['time']
        df_after_fvg = df[df['time'] > fvg_time].iloc[:-2]
        if (df_after_fvg['close'] < BULL_FVGS[i]['fvg_low']).any():
            del BULL_FVGS[i]
        else:
            i += 1


def filter_violated_bear(current, first):
    global BEAR_FVGS
    BEAR_FVGS = [fvg for fvg in BEAR_FVGS if current['close'] < fvg['fvg_high'] and fvg['time'] >= first['time']]

def filter_violated_bull(current, first):
    global BULL_FVGS
    BULL_FVGS = [fvg for fvg in BULL_FVGS if current['close'] > fvg['fvg_low'] and fvg['time'] >= first['time']]

def calculate_current_fvg(df):
    previous = df.iloc[-4]
    current = df.iloc[-3]
    next = df.iloc[-2]
    first = df.iloc[0]

    determine_fvg(previous, current, next)

    filter_violated_bear(current, first)
    filter_violated_bull(current, first)


def find_nearest_price(prices, target_price, threshold=600):
    closest_price = None
    min_gap = threshold + 1
    for price in prices:
        gap = abs(float(price) - float(target_price))
        if gap <= threshold and gap < min_gap:
            closest_price = price
            min_gap = gap
    return closest_price

def log_trade(side, entry, nearest_ssl_price, timestamp, fvg_high, fvg_low, fvg_time):
    stop_loss = nearest_ssl_price
    tp_difference = abs(float(entry) - float(nearest_ssl_price)) * 1
    if side == 'long':
        take_profit = float(entry) + tp_difference
    else:
        take_profit = float(entry) - tp_difference

    trade = {
        'side': side,
        'entry': entry,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'timestamp': timestamp,
        'fvg_high': fvg_high,
        'fvg_low': fvg_low,
        'fvg_time': fvg_time,
    }

    try:
        with open('trade_execution_log.json', 'r') as file:
            trade_log = json.load(file)
    except FileNotFoundError:
        trade_log = []

    trade_log.append(trade)

    with open('trade_execution_log.json', 'w') as file:
        json.dump(trade_log, file, indent=4)

def sliding_window(df, window_size=1500, step=1):
    for i in range(0, len(df) - window_size + 1, step):
        yield df.iloc[i:i+window_size]

def execute():
    df = pd.read_json('HistoricalData/btc_m5_10_days.json')

    global BULL_FVGS, BEAR_FVGS, LIQ_LEVELS
    BULL_FVGS = []
    BEAR_FVGS = []
    LIQ_LEVELS = []

    # Calculate total number of iterations
    total_iterations = len(df) - 1500 + 1


    # Use tqdm to display loading bar
    for i in tqdm(range(total_iterations), desc="Processing"):
        start_index = i
        end_index = i + 1500

        window_data = df.iloc[start_index:end_index]

        LIQ_LEVELS = get_nearest_liq_levels(window_data)

        if i == 0:
            calculate_full_window_fvg(window_data)
        else:
            calculate_current_fvg(window_data)

        latest_candle = window_data.iloc[-2]

        is_bull = latest_candle['close'] >= latest_candle['open']

        if is_bull:
            for x in BEAR_FVGS:
                if latest_candle['close'] > x['fvg_high']:
                    nearest_ssl_price = find_nearest_price([ssl['price'] for ssl in LIQ_LEVELS['SSL']], latest_candle['close'])
                    if nearest_ssl_price is not None:
                        log_trade('long', latest_candle['close'], nearest_ssl_price, latest_candle['time'], x['fvg_high'], x['fvg_low'], x['time'])
        else:
            for x in BULL_FVGS:
                if latest_candle['close'] < x['fvg_low']:
                    nearest_bsl_price = find_nearest_price([bsl['price'] for bsl in LIQ_LEVELS['BSL']], latest_candle['close'])
                    if nearest_bsl_price is not None:
                        log_trade('short', latest_candle['close'], nearest_bsl_price, latest_candle['time'], x['fvg_high'], x['fvg_low'], x['time'])

        LIQ_LEVELS = []

if __name__ == '__main__':
    if os.path.exists('trade_execution_log.json'):
        with open('trade_execution_log.json', 'w') as file:
            file.write('[]')

    execute()
    print('Complete Backtest')

    print('-------------------BREAKDOWN-------------------')

    calculate_trade_stats()