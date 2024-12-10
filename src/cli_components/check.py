from rich import print as rprint
from .utils import print_collection_stats
from datetime import datetime, timedelta


def check_analysis_results(db):
    """Check contents of analysis collections"""
    rprint(f"\n[bold blue]{'='*60}[/bold blue]")
    rprint("[bold green]Analysis Collections Status[/bold green]")
    rprint(f"[bold blue]{'='*60}[/bold blue]\n")

    # First print all collection stats
    for collection_name in ["weather_data", "eda_results", "pca_results", "ml_results"]:
        print_collection_stats(db[collection_name], collection_name)

    # Then analyze and print date range for weather_data
    collection = db["weather_data"]

    # Find earliest and latest dates
    earliest = collection.find_one({}, sort=[("tNow", 1)])
    latest = collection.find_one({}, sort=[("tNow", -1)])

    if earliest and latest:
        earliest_date = earliest["tNow"].date()
        latest_date = latest["tNow"].date()

        # Print overall range with proper formatting
        rprint("\n[bold cyan]Date Range in Database:[/bold cyan]")
        rprint("[cyan]From: {0}[/cyan]".format(earliest_date))
        rprint("[cyan]To:   {0}[/cyan]".format(latest_date))

        # Check for missing dates
        current_date = earliest_date
        missing_dates = []
        gap_start = None

        while current_date <= latest_date:
            # Check if this date exists in the database
            start_of_day = datetime.combine(current_date, datetime.min.time())
            end_of_day = datetime.combine(current_date, datetime.max.time())

            count = collection.count_documents(
                {"tNow": {"$gte": start_of_day, "$lte": end_of_day}}
            )

            if count == 0:
                if not gap_start:
                    gap_start = current_date
            else:
                if gap_start:
                    gap_days = (current_date - gap_start).days
                    if gap_days > 7:
                        missing_dates.append(
                            (
                                gap_start.strftime("%Y-%m-%d"),
                                (current_date - timedelta(days=1)).strftime("%Y-%m-%d"),
                            )
                        )
                    else:
                        # Add individual dates for small gaps
                        temp_date = gap_start
                        while temp_date < current_date:
                            missing_dates.append(temp_date.strftime("%Y-%m-%d"))
                            temp_date += timedelta(days=1)
                    gap_start = None

            current_date += timedelta(days=1)

        # Handle case where gap extends to the end
        if gap_start:
            gap_days = (latest_date - gap_start).days + 1
            if gap_days > 7:
                missing_dates.append(
                    (gap_start.strftime("%Y-%m-%d"), latest_date.strftime("%Y-%m-%d"))
                )
            else:
                temp_date = gap_start
                while temp_date <= latest_date:
                    missing_dates.append(temp_date.strftime("%Y-%m-%d"))
                    temp_date += timedelta(days=1)

        if missing_dates:
            rprint("\n[bold yellow]Missing Dates:[/bold yellow]")
            for date in missing_dates:
                if isinstance(date, tuple):
                    rprint(f"[yellow]• {date[0]} to {date[1]}[/yellow]")
                else:
                    rprint(f"[yellow]• {date}[/yellow]")
        rprint()  # Empty line for spacing
    else:
        rprint("\n[yellow]No data found in weather_data collection[/yellow]\n")
