import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json
from LiquidityLevels.liquidity_levels import get_nearest_liq_levels

def gap_valid(num1, num2):
    threshold = 60
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


def log_trade(side, entry, nearest_ssl_price, timestamp, fvg_high, fvg_low):

    stop_loss = nearest_ssl_price
    tp_difference = abs(float(entry) - float(nearest_ssl_price)) * 2
    if side == 'long':
        take_profit = float(entry) + float(tp_difference)
    else:
        take_profit = float(entry) - float(tp_difference)

    trade = {
        'side': side,
        'entry': entry,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
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

def find_nearest_price(prices, target_price, threshold=1000):
    closest_price = None
    min_gap = threshold + 1
    for price in prices:
        gap = abs(float(price) - float(target_price))
        if gap <= threshold and gap < min_gap:
            closest_price = price
            min_gap = gap
    return closest_price

def execute():
    global BULL_FVGS, BEAR_FVGS, LIQ_LEVELS
    BULL_FVGS = []
    BEAR_FVGS = []
    LIQ_LEVELS = []

    while True:
        now = datetime.now()
        current_minute = now.minute
        current_second = now.second

        if current_minute % 1 == 0 and current_second == 2:
            print(f"Checking @ {now}")
            LIQ_LEVELS = get_nearest_liq_levels()
            df = fetch_data()
            calculate_fvg(df)
            latest_candle = df.iloc[-2]

            is_bull = latest_candle['close'] >= latest_candle['open']

            if is_bull:
                for x in BEAR_FVGS:
                    if latest_candle['close'] > x['fvg_high']:
                        nearest_ssl_price = find_nearest_price([ssl['price'] for ssl in LIQ_LEVELS['SSL']], latest_candle['close'])
                        if nearest_ssl_price is not None:
                            print(f"market LONG @ {datetime.now()}")
                            log_trade('long', latest_candle['close'], nearest_ssl_price, datetime.now(), x['fvg_high'], x['fvg_low'])
            else:
                for x in BULL_FVGS:
                    if latest_candle['close'] < x['fvg_low']:
                        nearest_bsl_price = find_nearest_price([bsl['price'] for bsl in LIQ_LEVELS['BSL']], latest_candle['close'])
                        if nearest_bsl_price is not None:
                            print(f"market SHORT @ {datetime.now()}")
                            log_trade('short', latest_candle['close'], nearest_bsl_price, datetime.now(), x['fvg_high'], x['fvg_low'])

            BULL_FVGS = []
            BEAR_FVGS = []
            LIQ_LEVELS = []
            time.sleep(280)

if __name__ == '__main__':
    if os.path.exists('trade_execution_log.json'):
        with open('trade_execution_log.json', 'w') as file:
            file.write('[]')

    execute()
