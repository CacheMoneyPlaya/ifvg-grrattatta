import json

# Load trade execution log
with open('trade_execution_log.json', 'r') as f:
    trade_log = json.load(f)

# Load historical data
with open('HistoricalData/btc_m5_10_days.json', 'r') as f:
    historical_data = json.load(f)

wins = 0
losses = 0

for trade in trade_log:
    side = trade['side']
    entry_price = trade['entry']
    stop_loss = trade['stop_loss']
    take_profit = trade['take_profit']
    timestamp = trade['timestamp']

    # Find corresponding OHLC data for the trade timestamp
    corresponding_data = next(data for data in historical_data if data['time'] == timestamp)

    if side == 'long':
        # Loop through historical data from the timestamp until take_profit or stop_loss is reached
        for data in historical_data[historical_data.index(corresponding_data):]:
            close_price = float(data['close'])
            if close_price >= take_profit:
                wins += 1
                break
            elif close_price <= stop_loss:
                losses += 1
                break
    elif side == 'short':
        # Loop through historical data from the timestamp until stop_loss or take_profit is reached
        for data in historical_data[historical_data.index(corresponding_data):]:
            close_price = float(data['close'])
            if close_price >= stop_loss:
                losses += 1
                break
            elif close_price <= take_profit:
                wins += 1
                break

print(f"Total Wins: {wins}")
print(f"Total Losses: {losses}")
