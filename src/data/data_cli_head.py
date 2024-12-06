import os
from datetime import datetime
from pathlib import Path
from rich import print as rprint
import pandas as pd
import glob


def get_csv_path(date_str=None):
    data_dir = Path(__file__).parent

    if date_str:
        try:
            datetime.strptime(date_str, "%Y_%m_%d")
            csv_path = data_dir / f"{date_str}_weather_station_data.csv"
            if not csv_path.exists():
                rprint(f"[red]No data file found for {date_str}[/red]")
                return None
            return csv_path
        except ValueError:
            rprint("[red]Invalid date format. Use YYYY_MM_DD.[/red]")
            return None
    else:
        # Find earliest CSV file
        csv_files = glob.glob(str(data_dir / "*_weather_station_data.csv"))
        if not csv_files:
            rprint("[red]No CSV files found[/red]")
            return None
        return min(csv_files)


def show_head(date_str=None):
    csv_path = get_csv_path(date_str)
    if not csv_path:
        return

    try:
        df = pd.read_csv(csv_path)
        total_rows = len(df)
        if date_str:
            rprint(
                f"[green]First 5 out of {total_rows} total rows in {os.path.basename(csv_path)}:[/green]"
            )
            rprint(df.head().to_string())
        else:
            rprint(f"[green]Earliest data file: {os.path.basename(csv_path)}[/green]")
            rprint(f"First timestamp: {df.iloc[0]['tNow']}")
    except Exception as e:
        rprint(f"[red]Error reading CSV: {str(e)}[/red]")
