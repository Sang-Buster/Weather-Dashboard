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

DATA_DIR = Path(__file__).parent.parent / "data"


def process_chunk(args):
    """Process a chunk of the DataFrame and upload to MongoDB."""
    chunk_df, uri, date, chunk_id = args
    try:
        client = MongoClient(uri)
        db = client["weather_dashboard"]
        collection = db["weather_data"]

        # Convert timestamps only, no metadata
        chunk_df["tNow"] = pd.to_datetime(chunk_df["tNow"]).dt.tz_localize("UTC")

        # Convert directly to documents without metadata
        documents = chunk_df.apply(
            lambda row: {**row.to_dict(), "tNow": row["tNow"].to_pydatetime()}, axis=1
        ).tolist()

        # Insert documents
        collection.insert_many(documents, ordered=False)
        client.close()
        return True, len(documents)
    except Exception as e:
        return False, str(e)


def upload_csv_to_mongodb(
    start_date: str, end_date: str = None, db: Any = None
) -> bool:
    """Upload multiple dates using multiprocessing and chunking."""
    try:
        uri = st.secrets["mongo"]["uri"]

        # Generate list of dates
        start = datetime.strptime(start_date, "%Y_%m_%d")
        end = datetime.strptime(end_date, "%Y_%m_%d") if end_date else start
        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime("%Y_%m_%d"))
            current += timedelta(days=1)

        # Clear existing data for the date range
        collection = db["weather_data"]
        start_datetime = start.replace(hour=0, minute=0, second=0)
        end_datetime = (end if end_date else start).replace(
            hour=23, minute=59, second=59
        )

        # Delete documents within the date range
        result = collection.delete_many(
            {"tNow": {"$gte": start_datetime, "$lte": end_datetime}}
        )
        rprint(
            f"[yellow]Deleted {result.deleted_count:,} existing records for selected dates[/yellow]"
        )

        rprint(f"\n[bold blue]{'='*50}[/bold blue]")
        rprint(f"[bold green]Starting upload of {len(dates)} dates[/bold green]")
        rprint(f"[bold blue]{'='*50}[/bold blue]\n")

        # Create progress tracking
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=Console(force_terminal=True),
        )

        total_success = 0
        total_records = 0

        with progress:
            for date in dates:
                filename = os.path.join(DATA_DIR, f"{date}_weather_station_data.csv")
                if not os.path.exists(filename):
                    rprint(f"[red]File {filename} not found.[/red]")
                    continue

                # Read the CSV file
                df = pd.read_csv(filename)
                total_rows = len(df)

                # Calculate optimal chunk size and number of processes
                num_processes = min(cpu_count(), 8)  # Limit to 8 processes max
                chunk_size = ceil(
                    total_rows / (num_processes * 2)
                )  # Create 2 chunks per process

                # Create chunks
                chunks = [df[i : i + chunk_size] for i in range(0, len(df), chunk_size)]

                # Create progress task for this date
                task_id = progress.add_task(f"Date {date}", total=total_rows)

                # Prepare arguments for multiprocessing
                chunk_args = [(chunk, uri, date, i) for i, chunk in enumerate(chunks)]

                # Process chunks in parallel
                with Pool(processes=num_processes) as pool:
                    for success, result in pool.imap_unordered(
                        process_chunk, chunk_args
                    ):
                        if success:
                            records_processed = result
                            total_records += records_processed
                            progress.update(task_id, advance=records_processed)
                            total_success += 1
                        else:
                            rprint(f"[red]Error in chunk: {result}[/red]")

        # Summary
        rprint(f"\n[bold blue]{'='*50}[/bold blue]")
        rprint("[bold]Upload Summary:[/bold]")
        rprint(f"- Total dates processed: {len(dates)}")
        rprint(f"- [green]Total records uploaded: {total_records:,}[/green]")
        rprint(f"- [blue]Total chunks processed: {total_success}[/blue]")
        rprint(f"[bold blue]{'='*50}[/bold blue]\n")

        # After successful upload, show collection stats
        print_collection_stats(db["weather_data"], "Weather Data")

        return total_success > 0

    except Exception as e:
        rprint(f"\n[red]Error in upload process: {str(e)}[/red]")
        return False
