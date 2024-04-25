import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import time

BEAR_FVGS = []
BULL_FVGS = []

def fetch_data():
    url = "https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=5m&limit=1000"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.DataFrame(response.json(), columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')

        return df
    else:
        print("Failed to fetch data:", response.text)
        return None

def determine_fvg(previous, current, next):
        if (
            (previous['high'] >= current['open'] and (previous['high'] <= current['close'])) and
            (next['low'] <= current['close'] and next['low'] >= current['open']) and
            previous['high'] <= next['low']
        ):
            BULL_FVGS.append({
                'time': current['time'],
                'fvg_high': next['low'],
                'fvg_low': previous['high'],
            })
        elif (
                (previous['low'] <= current['open'] and previous['low'] >= current['close']) and
                (next['high'] >= current['close'] and next['high'] <= current['open']) and
                previous['low'] >= next['high']
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
        df_after_fvg = df[df['time'] > fvg_time]
        if (df_after_fvg['close'] > BEAR_FVGS[i]['fvg_high']).any():
            del BEAR_FVGS[i]
        else:
            i += 1

    i=0
    while i < len(BULL_FVGS):
        fvg_time = BULL_FVGS[i]['time']
        df_after_fvg = df[df['time'] > fvg_time]
        if (df_after_fvg['close'] < BULL_FVGS[i]['fvg_low']).any():
            del BULL_FVGS[i]
        else:
            i += 1


def execute():
    while True:
        now = datetime.now()
        current_minute = now.minute
        current_second = now.second
        if current_minute % 5 == 0 and current_second == 5:
            print(f"Checking @ {now}")  # Print the timestamp before fetching data
            df = fetch_data()
            calculate_fvg(df)
            latest_candle = df.iloc[-2]
            is_bull = latest_candle['close'] >= latest_candle['open']

            if is_bull:
                for x in BEAR_FVGS:
                    if latest_candle['close'] >= x['fvg_high']:
                        print(f"market long @ {latest_candle['close']} --- time: {latest_candle['time']} --- FVG: {x}")
            else:
                for x in BULL_FVGS:
                    if latest_candle['close'] <= x['fvg_low']:
                        print(f"market short @ {latest_candle['close']} --- time: {latest_candle['time']}  --- FVG: {x}")

if __name__ == '__main__':
    execute()
