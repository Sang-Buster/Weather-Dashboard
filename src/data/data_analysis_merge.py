import pandas as pd
from pathlib import Path
from typing import List, Optional


def load_csv_file(file_path: Path) -> Optional[pd.DataFrame]:
    """Load a single CSV file and convert timestamp."""
    try:
        df = pd.read_csv(file_path)
        df["tNow"] = pd.to_datetime(df["tNow"])
        print(f"Successfully loaded: {file_path.name}")
        return df
    except Exception as e:
        print(f"Error loading {file_path.name}: {str(e)}")
        return None


def merge_weather_data(input_directory: str | Path, output_file: str) -> bool:
    """Merge multiple weather station CSV files into a single file."""
    input_dir = Path(input_directory)
    csv_files = list(input_dir.glob("*_weather_station_data.csv"))

    if not csv_files:
        print("No weather station CSV files found in the specified directory.")
        return False

    # Load and process all CSV files
    dfs: List[pd.DataFrame] = []
    for file in csv_files:
        df = load_csv_file(file)
        if df is not None:
            dfs.append(df)

    if not dfs:
        print("No data frames were successfully loaded.")
        return False

    # Merge and process data
    merged_df = (
        pd.concat(dfs, ignore_index=True)
        .sort_values("tNow")
        .drop_duplicates(subset=["tNow"], keep="first")
    )

    # Save merged data
    output_path = input_dir / output_file
    merged_df.to_csv(output_path, index=False)
    print(f"Successfully merged {len(dfs)} files into {output_file}")
    print(f"Time range: {merged_df['tNow'].min()} to {merged_df['tNow'].max()}")
    return True


if __name__ == "__main__":
    merge_weather_data("src/data", "merged_weather_data.csv")
