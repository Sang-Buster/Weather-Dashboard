import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from rich import print as rprint
import io

from src import CSV_DIR

DATA_DIR = Path(CSV_DIR)


def spit_csv_data(start_date: str, end_date: str = None) -> tuple[str, io.StringIO]:
    """Read CSV data for the given date range and return as a StringIO object."""
    try:
        # Generate list of dates
        start = datetime.strptime(start_date, "%Y_%m_%d")
        end = datetime.strptime(end_date, "%Y_%m_%d") if end_date else start

        # Initialize empty list to store DataFrames
        dfs = []
        dates = []

        # Collect data for each date
        current = start
        while current <= end:
            date_str = current.strftime("%Y_%m_%d")
            filename = DATA_DIR / f"{date_str}_weather_station_data.csv"

            if not filename.exists():
                rprint(f"[red]Warning: File not found for {date_str}[/red]")
            else:
                df = pd.read_csv(filename)
                dfs.append(df)
                dates.append(date_str)

            current += timedelta(days=1)

        if not dfs:
            raise FileNotFoundError("No data files found for the specified date range")

        # Combine all DataFrames
        combined_df = pd.concat(dfs, ignore_index=True)

        # Create a buffer for the CSV data
        csv_buffer = io.StringIO()
        combined_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # Create filename for the output
        if len(dates) == 1:
            filename = f"{dates[0]}_weather_data.csv"
        else:
            filename = f"{dates[0]}_to_{dates[-1]}_weather_data.csv"

        return filename, csv_buffer

    except Exception as e:
        raise Exception(f"Error processing CSV data: {str(e)}")
