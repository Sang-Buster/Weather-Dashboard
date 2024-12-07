import os
from datetime import datetime
from pathlib import Path
from rich import print as rprint
import pandas as pd
import glob

from src import CSV_DIR


def get_csv_path(date_str=None):
    data_dir = Path(CSV_DIR)

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
        # Find latest CSV file
        csv_files = glob.glob(str(data_dir / "*_weather_station_data.csv"))
        if not csv_files:
            rprint("[red]No CSV files found[/red]")
            return None
        return max(csv_files)


def show_tail(date_str=None):
    csv_path = get_csv_path(date_str)
    if not csv_path:
        return

    try:
        df = pd.read_csv(csv_path)
        total_rows = len(df)
        
        if total_rows == 0:
            rprint(f"[yellow]The CSV file {os.path.basename(csv_path)} is empty[/yellow]")
            return
            
        if date_str:
            rprint(
                f"[green]Last 5 out of {total_rows} total rows in {os.path.basename(csv_path)}:[/green]"
            )
            rprint(df.tail().to_string())
        else:
            rprint(f"[green]Latest data file: {os.path.basename(csv_path)}[/green]")
            rprint(f"Last timestamp: {df.iloc[-1]['tNow']}")

            last_row = df.iloc[-1] # get last row of dataframe
            myStr='Temp={0:0.1f}(F), RH={1:0.1f}(%), P={2:0.1f}(Pa), WindSpd={3:0.1f}(mph)'.format( last_row['Temp_C']*(9/5)+32 , last_row['Hum_RH'] , last_row['Press_Pa'] , last_row['3DSpeed_m_s']*2.237 )
            rprint(f"[cyan]conditions as of [{last_row['tNow']}] {myStr}[/cyan]")

    except Exception as e:
        rprint(f"[red]Error reading CSV: {str(e)}[/red]")
