from datetime import datetime, timedelta
from rich import print as rprint
from pathlib import Path
import pandas as pd


def get_available_date_range():
    # Look for CSV files in src/data directory
    data_dir = Path(__file__).parent

    if not data_dir.exists():
        rprint("[red]Data directory not found.[/red]")
        return False

    dates = []
    file_info = []  # Store information about each file
    total_rows = 0
    total_size = 0

    for file in data_dir.glob("*_weather_station_data.csv"):
        try:
            # Extract date from filename
            date_str = file.name.split("_weather")[0]
            date = datetime.strptime(date_str, "%Y_%m_%d")
            dates.append(date)

            # Get file size in MB
            size_mb = file.stat().st_size / (1024 * 1024)
            total_size += size_mb

            # Get row count
            df = pd.read_csv(file)
            row_count = len(df)
            total_rows += row_count

            file_info.append((date, row_count, size_mb))
        except ValueError:
            continue

    if not dates:
        rprint("[yellow]No weather station data files found.[/yellow]")
        return False

    dates.sort()
    file_info.sort(key=lambda x: x[0])  # Sort by date

    # Find missing dates
    missing_dates = []
    if len(dates) > 1:
        for i in range(len(dates) - 1):
            delta = (dates[i + 1] - dates[i]).days
            if delta > 1:
                for j in range(1, delta):
                    missing_dates.append(dates[i] + timedelta(days=j))

    # Print results
    rprint(
        f"[green]Available date range: {dates[0].strftime('%m/%d/%Y')} to {dates[-1].strftime('%m/%d/%Y')}[/green]"
    )

    # Print file details
    rprint("\n[cyan]File Details:[/cyan]")
    for date, rows, size in file_info:
        rprint(
            f"[cyan]- {date.strftime('%m/%d/%Y')}: {rows:,} rows, {size:.2f} MB[/cyan]"
        )

    # Print totals
    rprint(f"\n[green]Total rows across all files: {total_rows:,}[/green]")
    rprint(f"[green]Total size of all files: {total_size:.2f} MB[/green]")

    if missing_dates:
        rprint("\n[yellow]Missing dates:[/yellow]")
        for date in missing_dates:
            rprint(f"[yellow]- {date.strftime('%m/%d/%Y')}[/yellow]")

    return True
