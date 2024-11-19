import pandas as pd
import glob
import os

def merge_weather_data(input_directory, output_file):
    # Get all CSV files that match the weather station data pattern
    csv_files = glob.glob(os.path.join(input_directory, "*_weather_station_data.csv"))
    
    if not csv_files:
        print("No weather station CSV files found in the specified directory.")
        return False
    
    # Create an empty list to store individual dataframes
    dfs = []
    
    # Read each CSV file and append to the list
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            # Convert tNow to datetime for proper sorting
            df['tNow'] = pd.to_datetime(df['tNow'])
            dfs.append(df)
            print(f"Successfully loaded: {os.path.basename(file)}")
        except Exception as e:
            print(f"Error loading {file}: {str(e)}")
    
    if not dfs:
        print("No data frames were successfully loaded.")
        return False
    
    # Concatenate all dataframes
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Sort by timestamp
    merged_df = merged_df.sort_values('tNow')
    
    # Remove any duplicate timestamps
    merged_df = merged_df.drop_duplicates(subset=['tNow'], keep='first')
    
    # Save the merged dataframe
    output_path = os.path.join(input_directory, output_file)
    merged_df.to_csv(output_path, index=False)
    

merge_weather_data(input_directory="src/data", output_file="merged_weather_data.csv")