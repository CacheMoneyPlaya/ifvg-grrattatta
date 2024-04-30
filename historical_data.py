import requests
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import warnings as w
import os
from datetime import datetime

w.filterwarnings("ignore")

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

symbol = "BTCUSDT"
interval = "5m"
num_sets = 2
data_sets = fetch_multiple_data(symbol, interval, num_sets=num_sets)

combined_data = []
for data in data_sets:
    combined_data.extend(data)

# Create DataFrame from combined data
df = pd.DataFrame(combined_data, columns=["time", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])

# Convert time column to readable datetime format
df['time'] = pd.to_datetime(df['time'], unit='ms')  # Convert from milliseconds to datetime objects

# Add an hour to each timestamp in the 'time' column (assuming British Summer Time)
df['time'] += pd.Timedelta(hours=1)

# Sort DataFrame by 'time' column in ascending order with milliseconds precision
df = df.sort_values(by='time')

# Directory to save the JSON file
directory = "HistoricalData"
if not os.path.exists(directory):
    os.makedirs(directory)

# Save DataFrame to JSON file with datetime format
df.to_json(os.path.join(directory, "btc_m5_10_days.json"), date_format='iso', orient='records')
