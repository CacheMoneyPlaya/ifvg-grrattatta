import json

# Load trade execution log
with open('trade_execution_log.json', 'r') as file:
    trade_log = json.load(file)

# Load historical data
with open('HistoricalData/btc_m5_10_days.json', 'r') as file:
    historical_data = json.load(file)

# Initialize variables
winning_trades = 0
losing_trades = 0
cumulative_profit = 0

def calculate_profit(trade):
    entry_price = trade['entry']
    stop_loss = trade['stop_loss']
    take_profit = trade['take_profit']
    side = trade['side']
    open_price = None

    # Find open price of the candle at the trade's timestamp
    for candle in historical_data:
        if candle['time'] == trade['timestamp']:
            open_price = float(candle['open'])
            break

    print(f"Trade: {trade['timestamp']}, Open Price: {open_price}")

    # Calculate profit or current profit if trade is still open
    if open_price:
        if side == 'long':
            position_size = 100 / (entry_price - stop_loss)  # Calculate position size
            profit = (open_price - entry_price) * position_size
            return profit
        elif side == 'short':
            position_size = 100 / (stop_loss - entry_price)  # Calculate position size
            profit = (entry_price - open_price) * position_size
            return profit
    else:
        return None  # Trade still open, profit is not calculated yet




# Iterate through trades and calculate profit
for trade in trade_log:
    profit = calculate_profit(trade)
    if profit is not None:
        cumulative_profit += profit
        if profit > 0:
            winning_trades += 1
        elif profit < 0:
            losing_trades += 1
        print(f"Trade closed at {trade['timestamp']}, Profit: {profit}")

# Output results
print("\n--- Results ---")
print(f"Total Winning Trades: {winning_trades}")
print(f"Total Losing Trades: {losing_trades}")
print(f"Cumulative Profit: {cumulative_profit}")
