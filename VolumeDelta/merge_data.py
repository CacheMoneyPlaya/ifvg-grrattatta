import json
from datetime import datetime, timedelta

# Load data from agg.json
with open('aggr_output.json', 'r') as f:
    agg_data = json.load(f)

# Shift timestamps in agg_data by one hour
for item in agg_data:
    time_obj = datetime.strptime(item['Date'], '%Y-%m-%d %H:%M:%S')
    shifted_time_obj = time_obj + timedelta(hours=1)
    item['Date'] = shifted_time_obj.strftime('%Y-%m-%d %H:%M:%S')

# Load data from data.json and convert timestamps to match the format in agg_data
with open('HistoricalData/btc_m5_current.json', 'r') as f:
    data_data = json.load(f)
    for item in data_data:
        # Convert timestamp format
        item['time'] = datetime.strptime(item['time'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')

# Create a dictionary to store Delta Volume values by timestamp from agg_data
delta_volume_dict = {item['Date']: item['Delta Volume'] for item in agg_data}

# Merge data and add Delta Volume from agg_data, remove items without data to merge
merged_data = []
for item in data_data:
    if item['time'] in delta_volume_dict:
        item['Delta Volume'] = delta_volume_dict[item['time']]
        merged_data.append(item)

# Write merged data to a new file
with open('merged_data.json', 'w') as f:
    json.dump(merged_data, f, indent=4)
