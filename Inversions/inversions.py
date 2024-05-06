import requests
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

candlesticks = [{"timestamp": c[0] / 1000, "open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4]), "volume": float(c[5])} for c in requests.get("https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=5m&limit=150").json()[:-1]]
df = pd.DataFrame(candlesticks).set_index(pd.to_datetime(pd.DataFrame(candlesticks)['timestamp'], unit='s'))

box_data = []

plt.rcParams.update({'ytick.color': 'w', 'xtick.color': 'w'})
fig, ax = plt.subplots(figsize=(18, 6))
mpf.plot(df, type='candle', style='classic', ylabel='', show_nontrading=True, ax=ax, axisoff=True, tight_layout=True, volume=False, scale_width_adjustment=dict(candle=0.6))

ax.spines[['top', 'right', 'bottom', 'left']].set_visible(False)

lines = {
    "green": {"visible": False, "value": None, "end_time": None},
    "red": {"visible": False, "value": None, "end_time": None}
}

for i in range(2, len(df)):
    if df['high'][i-2] < df['low'][i] and df['close'][i-1] - df['open'][i-1] > 0 and abs(df['high'][i-2] - df['low'][i]) > 110:
        ax.fill_between(df.index[i-2:i+1], df['high'][i-2], df['low'][i], color='gray', alpha=0.2, edgecolor=None)
        ax.plot([df.index[i-1], df.index[i-1] + pd.Timedelta(minutes=5) * 7], [df['high'][i-2], df['high'][i-2]], color='green', linestyle='-', linewidth=0.5, alpha=0.5)
        print(f"new_fvg_bullish: Time - {df.index[i-1]}, High - {df['low'][i]}, Low - {df['high'][i-2]}, Range - {round(abs(df['high'][i-2] - df['low'][i]) ,2)}")
        lines["green"]["visible"] = True
        lines["green"]["value"] = df['high'][i-2]
        lines["green"]["end_time"] = df.index[i-1] + pd.Timedelta(minutes=5) * 7

    if lines["green"]["visible"] and df['close'][i] < lines["green"]["value"] and df.index[i] <= lines["green"]["end_time"]:
        ax.plot(df.index[i], df['low'][i], 'ro', markersize=3)
        lines["green"]["visible"] = False

    if df['low'][i-2] > df['high'][i] and df['open'][i-1] - df['close'][i-1] > 0 and abs(df['low'][i-2] - df['high'][i]) > 110:
        ax.fill_between(df.index[i-2:i+1], df['low'][i-2], df['high'][i], color='gray', alpha=0.2, edgecolor=None)
        ax.plot([df.index[i], df.index[i] + pd.Timedelta(minutes=5) * 8], [df['low'][i-2], df['low'][i-2]], color='red', linestyle='-', linewidth=0.5, alpha=0.5)
        print(f"new_fvg_bearish: Time - {df.index[i-1]}, High - {df['low'][i-2]}, Low - {df['high'][i]}, Range - {round(abs(df['low'][i-2] - df['high'][i]),2)}")
        lines["red"]["visible"] = True
        lines["red"]["value"] = df['low'][i-2]
        lines["red"]["end_time"] = df.index[i] + pd.Timedelta(minutes=5) * 7

    if lines["red"]["visible"] and df['close'][i] > lines["red"]["value"] and df.index[i] <= lines["red"]["end_time"]:
        ax.plot(df.index[i], df['high'][i], 'go', markersize=3)
        lines["red"]["visible"] = False

plt.show()
