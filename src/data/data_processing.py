import pandas as pd
import numpy as np

# Read the CSV file
df = pd.read_csv("src/data/current_weather_data_logfile.csv")

# Convert tNow to datetime
df["tNow"] = pd.to_datetime(df["tNow"])


# Function to calculate statistics for a column
def get_stats(column):
    return {
        "median": np.median(column),
        "mean": np.mean(column),
        "min": np.min(column),
        "max": np.max(column),
        "range": np.ptp(column),  # Peak-to-peak (maximum - minimum)
    }


# Calculate statistics for each column (excluding 'tNow' and 'Error')
stats = {}
for column in df.columns:
    if column not in ["tNow", "Error"]:
        stats[column] = get_stats(df[column])

# Print the results
for column, data in stats.items():
    print(f"\n{column}:")
    print(f"  Median: {data['median']:.4f}")
    print(f"  Mean: {data['mean']:.4f}")
    print(f"  Min: {data['min']:.4f}")
    print(f"  Max: {data['max']:.4f}")
    print(f"  Range: {data['range']:.4f} ({data['min']:.4f} to {data['max']:.4f})")

# Calculate time range
time_range = df["tNow"].max() - df["tNow"].min()
print(f"\nTime range: {time_range}")
