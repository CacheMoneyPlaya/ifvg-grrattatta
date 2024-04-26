import os
import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

BEAR_FVGS = []
BULL_FVGS = []
DATA_FILE = 'btc_data.json'

def fetch_data():
    url = "https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=30m&limit=100"
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

def chart_data(df):
    fig = go.Figure(data=[go.Candlestick(x=df['time'],
                                         open=df['open'].astype(float),
                                         high=df['high'].astype(float),
                                         low=df['low'].astype(float),
                                         close=df['close'].astype(float),
                                         increasing_line_color='grey',
                                         decreasing_line_color='black',
                                         )])

    for i in range(1, len(df) - 2):
        previous = df.iloc[i - 1]
        current = df.iloc[i]
        next = df.iloc[i + 1]
        determine_fvg(previous, current, next)
        fig.add_shape(type='rect',
                      xref='x',
                      yref='y',
                      x0=current['time'],
                      y0=current['low'],
                      x1=current['time'],
                      y1=current['high'],
                      line=dict(width=0))
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

    for value in BEAR_FVGS:
        fig.add_shape(type='rect',
                      xref='x',
                      yref='y',
                      x0=value['time'],
                      y0=value['fvg_low'],
                      x1=df['time'].iloc[-1],
                      y1=value['fvg_high'],
                      fillcolor='red',
                      opacity=0.5,
                      line=dict(width=0))

    for value in BULL_FVGS:
        fig.add_shape(type='rect',
                      xref='x',
                      yref='y',
                      x0=value['time'],
                      y0=value['fvg_low'],
                      x1=df['time'].iloc[-1],
                      y1=value['fvg_high'],
                      fillcolor='green',
                      opacity=0.5,
                      line=dict(width=0))

    fig.update_layout(title='BTC/USDT',
                       xaxis_title='',
                       yaxis_title='')

    fig.show()


if __name__ == '__main__':
    data = fetch_data()
    if data is not None:
        chart_data(data)
