import pandas as pd

# List of input files
input_files = [
    "src/data/2024_10_08_weather_station_data.csv",
    "src/data/2024_10_09_weather_station_data.csv",
    "src/data/2024_10_10_weather_station_data.csv",
    "src/data/2024_10_11_weather_station_data.csv",
]

# Output file name
output_file = "src/data/current_weather_data_logfile.csv"

# Read and concatenate the data
dfs = []
for file in input_files:
    df = pd.read_csv(file)
    dfs.append(df)

combined_df = pd.concat(dfs, ignore_index=True)

# Sort the combined dataframe by the timestamp
combined_df["tNow"] = pd.to_datetime(combined_df["tNow"])
combined_df = combined_df.sort_values("tNow")

# Write the combined data to the output file
combined_df.to_csv(output_file, index=False)

print(f"Combined data has been written to {output_file}")
