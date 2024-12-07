from datetime import datetime, timedelta
from rich import print as rprint
from pathlib import Path
import pandas as pd

from src import CSV_DIR


def get_available_date_range(month=None):
    data_dir = Path(CSV_DIR)

    if not data_dir.exists():
        rprint("[red]Data directory not found.[/red]")
        return False

    # If month is provided, validate format
    target_date = None
    if month:
        try:
            target_date = datetime.strptime(month, "%Y_%m")
        except ValueError:
            rprint("[red]Invalid month format. Use YYYY_MM.[/red]")
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

            # Skip if month is specified and doesn't match
            if target_date and (
                date.year != target_date.year or date.month != target_date.month
            ):
                continue

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
        if month:
            rprint(f"[yellow]No weather station data files found for {month}.[/yellow]")
        else:
            rprint("[yellow]No weather station data files found.[/yellow]")
        return False

    dates.sort()
    file_info.sort(key=lambda x: x[0])  # Sort by date

    # Find missing dates
    missing_dates = []
    if len(dates) > 1:
        # If month is specified, we should check all days in that month
        if target_date:
            # Get the first and last day of the month
            first_day = target_date.replace(day=1)
            if target_date.month == 12:
                last_day = target_date.replace(
                    year=target_date.year + 1, month=1, day=1
                )
            else:
                last_day = target_date.replace(month=target_date.month + 1, day=1)

            # Create a set of all dates in the month
            all_dates = set()
            current = first_day
            while current < last_day:
                all_dates.add(current)
                current += timedelta(days=1)

            # Find missing dates by comparing with actual dates
            existing_dates = set(dates)
            missing_dates = sorted(list(all_dates - existing_dates))
        else:
            # Original logic for finding gaps in sequential dates
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
