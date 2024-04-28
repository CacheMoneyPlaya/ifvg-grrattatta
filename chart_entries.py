import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
import json

# Load trade execution log from JSON file
with open('trade_execution_log.json', 'r') as file:
    trade_execution_log = json.load(file)

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

# Fetch data
df = fetch_data()

# Create candlestick trace
candlestick_trace = go.Candlestick(x=df['time'],
                                    open=df['open'],
                                    high=df['high'],
                                    low=df['low'],
                                    close=df['close'],
                                    name='BTCUSDT')

# Create figure
fig = go.Figure(data=[candlestick_trace])

# Mark trades
for trade in trade_execution_log:
    trade_time = pd.to_datetime(trade['timestamp'])
    entry_price = float(trade['entry'])
    side = trade['side']

    # Find the index of the closest time in the dataframe
    idx = df['time'].sub(trade_time).abs().idxmin()

    if side == 'long':
        fig.add_trace(go.Scatter(x=[df['time'].iloc[idx]],
                                 y=[entry_price],
                                 mode='markers',
                                 marker=dict(color='green', symbol='x'),
                                 name='Long Trade'))
    elif side == 'short':
        fig.add_trace(go.Scatter(x=[df['time'].iloc[idx]],
                                 y=[entry_price],
                                 mode='markers',
                                 marker=dict(color='red', symbol='x'),
                                 name='Short Trade'))

# Update figure layout
fig.update_layout(title='BTCUSDT 5-minute Candlestick Chart with Trade Execution Points',
                  xaxis_title='Time',
                  yaxis_title='Price',
                  template='plotly_white')

# Show figure
fig.show()
