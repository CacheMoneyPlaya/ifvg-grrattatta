import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json

def gap_valid(num1, num2):
    threshold = 80
    num1 = float(num1)
    num2 = float(num2)

    spread = abs(num1 - num2)

    return spread >= threshold

def fetch_data():
    url = "https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=5m&limit=1500"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.DataFrame(response.json(), columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')

        df['time'] = df['time'] + timedelta(hours=1)

        return df
    else:
        print("Failed to fetch data:", response.text)
        return None

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

def calculate_fvg(df):
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


def log_trade(side, entry, timestamp, fvg_high, fvg_low):
    trade = {
        'side': side,
        'entry': entry,
        'timestamp': timestamp.isoformat(),
        'fvg_high': fvg_high,
        'fvg_low': fvg_low,
    }

    try:
        with open('trade_execution_log.json', 'r') as file:
            trade_log = json.load(file)
    except FileNotFoundError:
        trade_log = []

    trade_log.append(trade)

    with open('trade_execution_log.json', 'w') as file:
        json.dump(trade_log, file, indent=4)

def execute():
    global BULL_FVGS, BEAR_FVGS  # Add these lines
    BULL_FVGS = []  # initialize them here
    BEAR_FVGS = []
    while True:
        now = datetime.now()
        current_minute = now.minute
        current_second = now.second
        if current_minute % 5 == 0 and current_second == 2:
            print(f"Checking @ {now}")

            df = fetch_data()
            calculate_fvg(df)

            latest_candle = df.iloc[-2]

            is_bull = latest_candle['close'] >= latest_candle['open']

            if is_bull:
                for x in BEAR_FVGS:
                    if latest_candle['close'] > x['fvg_high']:
                        print(f"market LONG @ {datetime.now()}")
                        log_trade('long', latest_candle['close'], datetime.now(), x['fvg_high'], x['fvg_low'])
            else:
                for x in BULL_FVGS:
                    if latest_candle['close'] < x['fvg_low']:
                        print(f"market SHORT @ {datetime.now()}")
                        log_trade('short', latest_candle['close'], datetime.now(), x['fvg_high'], x['fvg_low'])
            BULL_FVGS = []
            BEAR_FVGS = []
            time.sleep(280)

if __name__ == '__main__':
    if os.path.exists('trade_execution_log.json'):
        with open('trade_execution_log.json', 'w') as file:
            file.write('[]')

    execute()