import os
import pandas as pd
from datetime import datetime, timedelta
from multiprocessing import Pool, cpu_count
from math import ceil
from pymongo import MongoClient
from rich import print as rprint
from rich.progress import (
    Progress,
    SpinnerColumn,
    TimeElapsedColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.console import Console
import streamlit as st
from .utils import print_collection_stats
from typing import Any
from pathlib import Path
import sys

from src import CSV_DIR

DATA_DIR = Path(CSV_DIR)


def process_chunk(args):
    """Process a chunk of the DataFrame and upload to MongoDB."""
    chunk_df, uri, date, chunk_id = args
    try:
        client = MongoClient(uri, w=0)
        db = client["weather_dashboard"]
        collection = db["weather_data"]

        # Convert timestamps only, no metadata
        chunk_df["tNow"] = pd.to_datetime(chunk_df["tNow"]).dt.tz_localize("UTC")

        # Convert directly to documents without metadata
        documents = chunk_df.apply(
            lambda row: {**row.to_dict(), "tNow": row["tNow"].to_pydatetime()}, axis=1
        ).tolist()

        # Use larger batch sizes for insert_many
        batch_size = 10000
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            collection.insert_many(batch, ordered=False)

        client.close()
        return True, len(documents)
    except Exception as e:
        return False, str(e)


def append_csv_to_mongodb(
    start_date: str = None, end_date: str = None, db: Any = None
) -> bool:
    """Append data for specific dates, overwriting existing data for those dates only."""
    try:
        if db is None:
            rprint("[red]Error: Database connection not provided[/red]")
            return False

        uri = st.secrets["mongo"]["uri"]
        collection = db["weather_data"]

        # Calculate dates
        if not start_date:
            rprint("[red]Error: Start date is required for append operation[/red]")
            return False

        start = datetime.strptime(start_date, "%Y_%m_%d")
        if end_date:
            end = datetime.strptime(end_date, "%Y_%m_%d")
        else:
            end = start

        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime("%Y_%m_%d"))
            current += timedelta(days=1)

        rprint(f"\n[bold blue]{'='*50}[/bold blue]")
        rprint(f"[bold green]Starting append of {len(dates)} dates[/bold green]")
        rprint(f"[bold blue]{'='*50}[/bold blue]\n")

        total_success = 0
        total_records = 0

        # Check if we're running in Discord bot context
        is_discord = "discord" in str(sys.modules)

        if is_discord:
            # Simpler output for Discord
            for date in dates:
                filename = os.path.join(DATA_DIR, f"{date}_weather_station_data.csv")
                if not os.path.exists(filename):
                    rprint(f"[red]File {filename} not found.[/red]")
                    continue

                # Delete existing data for this date
                date_start = datetime.strptime(date, "%Y_%m_%d").replace(
                    hour=0, minute=0, second=0
                )
                date_end = datetime.strptime(date, "%Y_%m_%d").replace(
                    hour=23, minute=59, second=59
                )
                collection.delete_many({"tNow": {"$gte": date_start, "$lte": date_end}})

                df = pd.read_csv(filename)
                total_rows = len(df)

                # Process chunks
                num_processes = min(cpu_count(), 8)
                chunk_size = ceil(total_rows / num_processes)
                chunks = [df[i : i + chunk_size] for i in range(0, len(df), chunk_size)]
                chunk_args = [(chunk, uri, date, i) for i, chunk in enumerate(chunks)]

                with Pool(processes=num_processes) as pool:
                    for success, result in pool.imap_unordered(
                        process_chunk, chunk_args
                    ):
                        if success:
                            total_records += result
                            total_success += 1
                        else:
                            rprint(f"[red]Error in chunk: {result}[/red]")

                rprint(f"[green]Processed {date}: {total_rows:,} records[/green]")
        else:
            # Progress bar output for CLI
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=Console(force_terminal=True),
            ) as progress:
                for date in dates:
                    filename = os.path.join(
                        DATA_DIR, f"{date}_weather_station_data.csv"
                    )
                    if not os.path.exists(filename):
                        rprint(f"[red]File {filename} not found.[/red]")
                        continue

                    # Delete existing data for this date
                    date_start = datetime.strptime(date, "%Y_%m_%d").replace(
                        hour=0, minute=0, second=0
                    )
                    date_end = datetime.strptime(date, "%Y_%m_%d").replace(
                        hour=23, minute=59, second=59
                    )
                    deleted = collection.delete_many(
                        {"tNow": {"$gte": date_start, "$lte": date_end}}
                    )
                    rprint(
                        f"[yellow]Deleted {deleted.deleted_count:,} existing records for {date}[/yellow]"
                    )

                    df = pd.read_csv(filename)
                    total_rows = len(df)

                    task_id = progress.add_task(f"Date {date}", total=total_rows)

                    num_processes = min(cpu_count(), 8)
                    chunk_size = ceil(total_rows / num_processes)
                    chunks = [
                        df[i : i + chunk_size] for i in range(0, len(df), chunk_size)
                    ]
                    chunk_args = [
                        (chunk, uri, date, i) for i, chunk in enumerate(chunks)
                    ]

                    with Pool(processes=num_processes) as pool:
                        for success, result in pool.imap_unordered(
                            process_chunk, chunk_args
                        ):
                            if success:
                                total_records += result
                                progress.update(task_id, advance=result)
                                total_success += 1
                            else:
                                rprint(f"[red]Error in chunk: {result}[/red]")

        # Summary
        rprint(f"\n[bold blue]{'='*50}[/bold blue]")
        rprint("[bold]Append Summary:[/bold]")
        rprint(f"- Total dates processed: {len(dates)}")
        rprint(f"- [green]Total records appended: {total_records:,}[/green]")
        rprint(f"- [blue]Total chunks processed: {total_success}[/blue]")
        rprint(f"[bold blue]{'='*50}[/bold blue]\n")

        # Show collection stats
        print_collection_stats(collection, "Weather Data")

        return total_success > 0

    except Exception as e:
        rprint(f"\n[red]Error in append process: {str(e)}[/red]")
        return False
