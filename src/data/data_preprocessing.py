import pandas as pd
import numpy as np

# Read the CSV file
df = pd.read_csv("src/data/2024_10_08_weather_station_data.csv")

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

# Check for errors
error_rows = df[df["Error"] > 0.0]
total_errors = len(error_rows)

print(f"\nTotal number of errors: {total_errors}")

if total_errors > 0:
    print("\nError details:")
    for index, row in error_rows.iterrows():
        print(f"Row {index + 2}: Time = {row['tNow']}, Error value = {row['Error']}")
else:
    print("No errors found in the dataset.")
