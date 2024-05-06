import requests
from urllib.parse import unquote
from datetime import datetime
from collections import defaultdict
import json as json_module
import json


spot_list = [
    "BITFINEX:BTCUSD" ,
    "COINBASE:BTC-USD" ,
    "BINANCE:btcusdt" ,
    "BINANCE:btcbusd" ,
    "BITGET:BTCUSDT" ,
    "BITFINEX: BTCUST" ,
    "BITFINEX:BTCF0:USTF0" ,
    "COINBASE:BTC-USDT" ,
    "BITSTAMP:btcusd"
]

perp_list = [
    "BINANCE_FUTURES:btcusd_perp",
    "BITMEX:XBTUSD" ,
    "BYBIT:BTCUSD" ,
    "DERIBIT:BTC-PERPETUAL" ,
    "BINANCE_FUTURES:btcusdt" ,
    "BINANCE_FUTURES:btcbusd" ,
    "BITGET:BTCUSDT_UMCBL" ,
    "BITFINEX:BTCF0:USTF0" ,
    "BITMEX:XBTUSDT" ,
    "BYBIT:BTCUSDT"  ,
    "KRAKEN:API_XBTUSD" ,
    "OKEX:BTC-USD-SWAP" ,
    "OKEX:BTC-USDT-SWAP"
]

def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def calculate_rounded_average(data_dict, field_name, count):
    total_sum = data_dict[field_name + "_sum"]
    if count > 0:
        avg = total_sum / count
        return f"{avg:.2f}"
    else:
        return "0.00"

spot_param = '%2B'.join(spot_list)
perp_param = '%3A'.join(perp_list)

current_time = datetime.now().timestamp() * 1000
rounded_time = round(current_time / 10000) * 10000

output_json_file_name = "aggr_output.json"

include_spot_param = True  # Set it to True if you want to include spot_param, False otherwise
include_perp_param = True  # Set it to True if you want to include perp_param, False otherwise

tensor_interval = []
# interval = 5000;     lookback = 27600000           #5 seconds
# interval = 15000;    lookback = 79800000           #15 seconds
# interval = 30000;    lookback = 101880000          #30 seconds
# interval = 60000;     lookback = 266400000         #1 minute
# interval = 300000;   lookback = 1474560000           #5 minute - 17 days of data
interval = 900000;   lookback = 5011200000         #15 minute - 52 days of data
# interval = 1800000;  lookback = 9936000000         #30 minute
# interval = 3600000;  lookback = 19785600000        #1 hour
# interval = 7200000;  lookback = 33696000000        #2 hour
# interval = 14400000; lookback = 810208870400       #4 hours
# interval = 21600000; lookback = 1377381916160      #6 hours
# interval = 28800000; lookback = 2331759269480      #8 hours
# interval = 43200000; lookback = 3961990754116      #12 hours
# interval = 86400000; lookback = 6738088704000      #1 day

first_time_span = rounded_time - lookback



param_to_include = spot_param if include_spot_param else perp_param

api_url = f"https://api.aggr.trade/historical/{first_time_span}/{int(rounded_time)}/{interval}/{unquote(param_to_include)}%2B{unquote(perp_param) if include_perp_param else ''}"


response = requests.get(api_url)
data = response.json() if response.status_code == 200 else {"results": []}

aggregated_data = defaultdict(lambda: {
    "Cbuy_sum": 0,
    "Close_sum": 0,
    "Csell_sum": 0,
    "High_sum": 0,
    "Lbuy_sum": 0,
    "Low_sum": 0,
    "Lsell_sum": 0,
    "Open_sum": 0,
    "Vbuy_sum": 0,
    "Vsell_sum": 0,
    "Count": 0
})

for result in data.get("results", []):
    try:
        time, cbuy, close, csell, high, lbuy, low, lsell, market, open_price, vbuy, vsell = result

        cbuy_float = to_float(cbuy)
        close_float = to_float(close)
        csell_float = to_float(csell)
        high_float = to_float(high)
        lbuy_float = to_float(lbuy)
        low_float = to_float(low)
        lsell_float = to_float(lsell)
        open_price_float = to_float(open_price)
        vbuy_float = to_float(vbuy)
        vsell_float = to_float(vsell)

        if time is not None:
            time = int(time)
            aggregated_data[time]["Cbuy_sum"] += cbuy_float if cbuy_float is not None else 0
            aggregated_data[time]["Close_sum"] += close_float if close_float is not None else 0
            aggregated_data[time]["Csell_sum"] += csell_float if csell_float is not None else 0
            aggregated_data[time]["High_sum"] += high_float if high_float is not None else 0
            aggregated_data[time]["Lbuy_sum"] += lbuy_float if lbuy_float is not None else 0
            aggregated_data[time]["Low_sum"] += low_float if low_float is not None else 0
            aggregated_data[time]["Lsell_sum"] += lsell_float if lsell_float is not None else 0
            aggregated_data[time]["Open_sum"] += open_price_float if open_price_float is not None else 0
            aggregated_data[time]["Vbuy_sum"] += vbuy_float if vbuy_float is not None else 0
            aggregated_data[time]["Vsell_sum"] += vsell_float if vsell_float is not None else 0
            aggregated_data[time]["Count"] += 1
    except (ValueError, TypeError):
        pass

aggregated_data_list = []

for time, result in sorted(aggregated_data.items()):
    count = result["Count"]
    aggregated_result = {
        "Time": time,
        "Open": calculate_rounded_average(result, 'Open', count),
        "High": calculate_rounded_average(result, 'High', count),
        "Low": calculate_rounded_average(result, 'Low', count),
        "Close": calculate_rounded_average(result, 'Close', count),
        "Cbuy": calculate_rounded_average(result, 'Cbuy', count),
        "Csell": calculate_rounded_average(result, 'Csell', count),
        "Lbuy": calculate_rounded_average(result, 'Lbuy', count),
        "Lsell": calculate_rounded_average(result, 'Lsell', count),
        "Vbuy": calculate_rounded_average(result, 'Vbuy', count),
        "Vsell": calculate_rounded_average(result, 'Vsell', count)
    }
    aggregated_data_list.append(aggregated_result)

output_data = aggregated_data_list

with open(output_json_file_name, "w") as json_file:
    json_module.dump(output_data, json_file, indent=4)

if response.status_code != 200:
    print(f"Failed to fetch data. Status code: {response.status_code}")

def calculate_deltas(data):
    for entry in data:
        entry['Vdelta'] = "{:.2f}".format(float(entry['Vbuy']) - float(entry['Vsell']))
        entry['Cdelta'] = "{:.2f}".format(float(entry['Cbuy']) - float(entry['Csell']))

def process_json_file(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            calculate_deltas(data)
        with open(filename, 'w') as file:
            json.dump(data, file, indent=2)

    except FileNotFoundError:
        print(f"The file '{filename}' was not found.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in '{filename}'.")

if __name__ == "__main__":
    filename = output_json_file_name
    process_json_file(filename)

def calculate_time_difference(data):
    start_time = data[0]["Time"]
    end_time = data[-1]["Time"]
    start_datetime = datetime.fromtimestamp(start_time)
    end_datetime = datetime.fromtimestamp(end_time)
    time_difference = end_datetime - start_datetime
    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return days, hours, minutes

if __name__ == "__main__":
    filename = output_json_file_name
    with open(filename, 'r') as file:
        data = json.load(file)
        days, hours, minutes = calculate_time_difference(data)
        print(f"Total time duration saved in json file: {days} days, {hours} hours, {minutes} minutes")


field_mapping = {
    "Cbuy": "Buy Trade Count",
    "Csell": "Sell Trade Count",
    "Lbuy": "Buy Liquidations",
    "Lsell": "Sell Liquidations",
    "Vbuy": "Buy Volume",
    "Vsell": "Sell Volume",
    "Vdelta": "Delta Volume",
    "Cdelta": "Delta Trade Count"
}


file_path = output_json_file_name
with open(file_path, "r") as file:
    data = json.load(file)

for entry in data:
    for old_field, new_field in field_mapping.items():
        if old_field in entry:
            entry[new_field] = entry.pop(old_field)

with open(file_path, "w") as file:
    json.dump(data, file, indent=4)

with open('aggr_output.json', 'r') as file:
    data = json.load(file)

def seconds_to_datetime(seconds):
    return datetime.utcfromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')

for entry in data:
    entry['Date'] = seconds_to_datetime(entry['Time'])
    entry['Date'] = entry['Date']

with open('aggr_output.json', 'w') as file:
    json.dump(data, file, indent=4)
