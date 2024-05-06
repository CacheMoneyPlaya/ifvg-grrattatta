import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json
from tqdm import tqdm
from LiquidityLevels.liquidity_levels import get_nearest_liq_levels
from VolumeDelta.backtest_volume_results import calculate_trade_stats

def find_nearest_price(prices, target_price, threshold=1000):
    closest_price = None
    min_gap = threshold + 1
    for price in prices:
        gap = abs(float(price) - float(target_price))
        if gap <= threshold and gap < min_gap:
            closest_price = price
            min_gap = gap
    return closest_price

def log_trade(side, entry, nearest_ssl_price, timestamp):
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
    df = pd.read_json('VolumeDelta/merged_data.json')

    global LIQ_LEVELS
    LIQ_LEVELS = []

    # Calculate total number of iterations
    total_iterations = len(df) - 1500 + 1

    count = 0

    # Use tqdm to display loading bar
    for i in tqdm(range(total_iterations), desc="Processing"):
        start_index = i
        end_index = i + 1500

        window_data = df.iloc[start_index:end_index]

        LIQ_LEVELS = get_nearest_liq_levels(window_data)

        latest_candle = window_data.iloc[-2]

        is_bull = latest_candle['close'] >= latest_candle['open']

        if latest_candle['Delta Volume'] >= 10000000:
            nearest_ssl_price = find_nearest_price([ssl['price'] for ssl in LIQ_LEVELS['SSL']], latest_candle['close'])

            nearest_ssl_price = float(latest_candle['close']) - 200.00
            if nearest_ssl_price is not None:
                log_trade('long', latest_candle['close'], nearest_ssl_price, latest_candle['time'])

        if latest_candle['Delta Volume'] <= -10000000:
            nearest_bsl_price = find_nearest_price([bsl['price'] for bsl in LIQ_LEVELS['BSL']], latest_candle['close'])

            nearest_bsl_price = float(latest_candle['close']) + 200.00
            if nearest_bsl_price is not None:
                log_trade('short', latest_candle['close'], nearest_bsl_price, latest_candle['time'])

        LIQ_LEVELS = []

    print(count)

if __name__ == '__main__':
    if os.path.exists('trade_execution_log.json'):
        with open('trade_execution_log.json', 'w') as file:
            file.write('[]')

    execute()
    print('Complete Backtest')

    print('-------------------BREAKDOWN-------------------')

    calculate_trade_stats('VolumeDelta/aggr_output.json')
