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
        # First verify the file has content
        with open(csv_path, "r") as f:
            lines = f.readlines()

        if len(lines) <= 1:  # Only header or empty file
            rprint(
                f"[yellow]Warning: File {os.path.basename(csv_path)} is empty or contains only headers[/yellow]"
            )
            return

        total_rows = len(lines) - 1  # -1 for header

        # Define column names based on the metadata
        columns = [
            "tNow",
            "u_m_s",
            "v_m_s",
            "w_m_s",
            "2dSpeed_m_s",
            "3DSpeed_m_s",
            "Azimuth_deg",
            "Elev_deg",
            "Press_Pa",
            "Temp_C",
            "Hum_RH",
            "SonicTemp_C",
            "Error",
        ]

        if date_str:
            # Read only the last 5 rows when date is specified
            df = pd.read_csv(
                csv_path, skiprows=max(1, total_rows - 4), names=columns
            )  # Changed from 0 to 1 to skip header

            # Create display DataFrame with rounded values (2 decimal places)
            df_display = pd.DataFrame(
                {
                    "Timestamp": pd.to_datetime(df["tNow"]).dt.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),  # Format timestamp
                    "Pressure (Pa)": df["Press_Pa"].round(2),
                    "Temp (°F)": (df["Temp_C"].astype(float) * 9 / 5 + 32).round(2),
                    "RH (%)": df["Hum_RH"].round(2),
                    "3D Wind Speed (mph)": (
                        df["3DSpeed_m_s"].astype(float) * 2.23694
                    ).round(2),
                }
            )

            rprint(
                f"[green]Last {len(df)} out of {total_rows} total rows in {os.path.basename(csv_path)}:[/green]"
            )
            rprint(df_display.to_string(index=False))
        else:
            # Read only the last row when no date
            df = pd.read_csv(
                csv_path, skiprows=max(1, total_rows - 1), names=columns
            )  # Changed from 0 to 1
            if len(df) == 0:
                rprint("[yellow]Warning: No data rows found in file[/yellow]")
                return

            last_row = df.iloc[-1]
            rprint(f"[green]Latest data file: {os.path.basename(csv_path)}[/green]")
            rprint(
                f"Timestamp: {pd.to_datetime(last_row['tNow']).strftime('%Y-%m-%d %H:%M:%S')}"
            )
            rprint(f"Pressure: {float(last_row['Press_Pa']):.2f} Pa")
            rprint(f"Temperature: {(float(last_row['Temp_C']) * 9/5 + 32):.2f}°F")
            rprint(f"Relative Humidity: {float(last_row['Hum_RH']):.2f}%")
            rprint(
                f"3D Wind Speed: {(float(last_row['3DSpeed_m_s']) * 2.23694):.2f} mph"
            )
    except Exception as e:
        rprint(f"[red]Error reading CSV: {str(e)}[/red]")
