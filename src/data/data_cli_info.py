from datetime import datetime, timedelta
from rich import print as rprint
from pathlib import Path


def get_available_date_range():
    # Look for CSV files in src/data directory
    data_dir = Path(__file__).parent

    if not data_dir.exists():
        rprint("[red]Data directory not found.[/red]")
        return False

    dates = []
    for file in data_dir.glob("*_weather_station_data.csv"):
        try:
            # Extract date from filename
            date_str = file.name.split("_weather")[0]
            date = datetime.strptime(date_str, "%Y_%m_%d")
            dates.append(date)
        except ValueError:
            continue

    if not dates:
        rprint("[yellow]No weather station data files found.[/yellow]")
        return False

    dates.sort()

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

    if missing_dates:
        rprint("\n[yellow]Missing dates:[/yellow]")
        for date in missing_dates:
            rprint(f"[yellow]- {date.strftime('%m/%d/%Y')}[/yellow]")

    return True
