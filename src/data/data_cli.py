import os
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta, UTC
import argparse
import streamlit as st
import json
from data_analysis_eda import main as run_eda
from data_analysis_pca import main as run_pca
from data_analysis_ml import main as run_ml
from typing import Any
from rich.progress import (
    Progress,
    SpinnerColumn,
    TimeElapsedColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.console import Console
from rich import print as rprint
from multiprocessing import Pool, cpu_count
from math import ceil
from data_cli_utils import print_banner

# Constants
COLLECTIONS_CONFIG = {
    "weather_data": {"timeseries": {"timeField": "tNow", "granularity": "seconds"}},
    "eda_results": {},
    "pca_results": {},
    "ml_results": {},
}

BATCH_SIZE = 10000
DATA_DIR = "src/data"


def connect_to_mongodb() -> Any:
    """Establish MongoDB connection and initialize time series collection."""
    client = MongoClient(
        st.secrets["mongo"]["uri"],
        maxPoolSize=100,  # Increased for parallel operations
        minPoolSize=20,  # More ready connections
        maxIdleTimeMS=45000,  # Longer idle timeout for connection reuse
        connectTimeoutMS=2000,  # Quick connection timeout
        socketTimeoutMS=30000,  # Longer socket timeout for large data transfers
        serverSelectionTimeoutMS=5000,  # Quick server selection
        retryWrites=True,
        retryReads=True,
        compressors=["zstd"],  # Best compression/speed ratio
        maxConnecting=8,  # More parallel connections
        w="majority",  # Ensure consistency
        readPreference="secondaryPreferred",  # Read from secondaries when possible
    )
    db = client["weather_dashboard"]

    # Check if collection exists
    if "weather_data" not in db.list_collection_names():
        print("Creating time series collection...")
        db.create_collection(
            "weather_data", timeseries={"timeField": "tNow", "granularity": "seconds"}
        )

    # Ensure index exists (will not recreate if already exists)
    db["weather_data"].create_index([("tNow", 1)])
    return db


def _print_collection_stats(collection: Any, collection_name: str) -> None:
    """Helper function to print collection statistics and preview."""
    total_docs = collection.count_documents({})
    rprint(f"\n[bold blue]{'='*60}[/bold blue]")
    rprint(f"[bold green]{collection_name} Collection Stats[/bold green]")
    rprint(f"[bold blue]{'='*60}[/bold blue]")
    rprint(f"Total Records: {total_docs:,}")

    if total_docs > 0:
        rprint("\n[bold]First document structure:[/bold]")
        first_doc = collection.find_one({}, {"_id": 0})
        if first_doc:

            def get_type_info(value):
                if isinstance(value, dict):
                    return {k: get_type_info(v) for k, v in value.items()}
                elif isinstance(value, list):
                    return (
                        f"<list[{type(value[0]).__name__}]>"
                        if value
                        else "<empty_list>"
                    )
                else:
                    return f"<{type(value).__name__}>"

            structure = get_type_info(first_doc)
            rprint(json.dumps(structure, indent=2))
    rprint(f"[bold blue]{'='*60}[/bold blue]\n")


def run_eda_analysis(db):
    """Run EDA analysis and upload results"""
    rprint(f"\n[bold blue]{'='*60}[/bold blue]")
    rprint("[bold green]Running EDA Analysis[/bold green]")
    rprint(f"[bold blue]{'='*60}[/bold blue]\n")

    # Run analysis
    run_eda()  # This creates correlation_data.json
    run_pca()  # This creates pca_data.json

    try:
        # Upload EDA results
        with open("src/data/data_analysis_result/correlation_data.json", "r") as f:
            correlation_data = json.load(f)
        collection = db["eda_results"]
        collection.delete_many({})
        collection.insert_one(
            {
                "type": "correlation_data",
                "data": correlation_data,
                "timestamp": datetime.now(UTC),
            }
        )
        _print_collection_stats(collection, "EDA Results")

        # Upload PCA results
        with open("src/data/data_analysis_result/pca_data.json", "r") as f:
            pca_data = json.load(f)
        collection = db["pca_results"]
        collection.delete_many({})
        collection.insert_one(
            {"type": "pca_data", "data": pca_data, "timestamp": datetime.now(UTC)}
        )
        _print_collection_stats(collection, "PCA Results")

    except FileNotFoundError as e:
        rprint(f"[red]Error: {str(e)}[/red]")


def run_pca_analysis(db):
    """Run PCA analysis and upload results"""
    # Run PCA analysis
    run_pca()  # This creates data_analysis_result/pca_data.json

    try:
        with open("src/data/data_analysis_result/pca_data.json", "r") as f:
            pca_data = json.load(f)

        # First, delete any existing documents in the collection
        collection = db["pca_results"]
        collection.delete_many({})  # Clear existing documents

        # Create new document
        document = {
            "type": "pca_data",
            "data": pca_data,
            "timestamp": datetime.now(UTC),
        }

        # Insert new document
        collection.insert_one(document)
        print("PCA results uploaded to MongoDB")
    except FileNotFoundError:
        print("Error: pca_data.json not found")


def run_ml_analysis(db):
    """Run ML analysis and upload results"""
    rprint(f"\n[bold blue]{'='*60}[/bold blue]")
    rprint("[bold green]Running ML Analysis[/bold green]")
    rprint(f"[bold blue]{'='*60}[/bold blue]\n")

    # Run ML analysis
    run_ml()

    try:
        collection = db["ml_results"]
        collection.delete_many({})

        # Load and upload ML plot data
        with open("src/data/data_analysis_result/ml_plot_data.json", "r") as f:
            ml_plot_data = json.load(f)

        # Load and upload ML prediction data
        with open("src/data/data_analysis_result/ml_prediction_data.json", "r") as f:
            ml_prediction_data = json.load(f)

        # Create documents
        documents = [
            {
                "type": "ml_plot_data",
                "data": ml_plot_data,
                "timestamp": datetime.now(UTC),
            },
            {
                "type": "ml_prediction_data",
                "data": ml_prediction_data,
                "timestamp": datetime.now(UTC),
            },
        ]

        # Insert new documents
        collection.insert_many(documents)
        _print_collection_stats(collection, "ML Results")

    except FileNotFoundError as e:
        rprint(f"[red]Error: {str(e)}[/red]")


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
        _print_collection_stats(db["weather_data"], "Weather Data")

        return total_success > 0

    except Exception as e:
        rprint(f"\n[red]Error in upload process: {str(e)}[/red]")
        return False


def delete_mongodb_collection(db):
    """Delete the weather data collection"""
    collection = db["weather_data"]
    result = collection.delete_many({})
    rprint(
        f"[green]Deleted {result.deleted_count:,} documents from the collection.[/green]"
    )
    return result.acknowledged


def check_analysis_results(db):
    """Check contents of analysis collections"""
    rprint(f"\n[bold blue]{'='*60}[/bold blue]")
    rprint("[bold green]Analysis Collections Status[/bold green]")
    rprint(f"[bold blue]{'='*60}[/bold blue]\n")

    for collection_name in ["weather_data", "eda_results", "pca_results", "ml_results"]:
        _print_collection_stats(db[collection_name], collection_name)


def main():
    print_banner()
    parser = argparse.ArgumentParser(
        description="Weather data management CLI",
        usage="meteorix [-h] {upload,delete,eda,ml,check} ...",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Upload command
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload weather data to MongoDB",
        description="Upload weather station data from CSV files to MongoDB.",
    )
    upload_parser.add_argument("start_date", help="Start date (YYYY_MM_DD)")
    upload_parser.add_argument(
        "end_date", nargs="?", help="End date (YYYY_MM_DD, optional)"
    )

    # Delete command
    subparsers.add_parser(
        "delete",
        help="Delete weather data collection",
        description="Delete all weather data from MongoDB collection.",
    )

    # EDA command
    subparsers.add_parser(
        "eda",
        help="Run EDA analysis",
        description="Perform exploratory data analysis and upload results.",
    )

    # ML command
    subparsers.add_parser(
        "ml",
        help="Run ML analysis",
        description="Perform machine learning analysis and upload results.",
    )

    # Check command
    subparsers.add_parser(
        "check",
        help="Check analysis results",
        description="Display contents of analysis collections in MongoDB.",
    )

    args = parser.parse_args()
    db = connect_to_mongodb()

    try:
        if args.command == "check":
            check_analysis_results(db)
            return

        if args.command == "delete":
            if delete_mongodb_collection(db):
                rprint("[green]Collection deleted successfully.[/green]")
            else:
                rprint("[red]Failed to delete collection.[/red]")
            return

        elif args.command == "eda":
            run_eda_analysis(db)
            run_pca_analysis(db)
            _print_collection_stats(db["eda_results"], "EDA Results")
            _print_collection_stats(db["pca_results"], "PCA Results")
            return

        elif args.command == "ml":
            run_ml_analysis(db)
            _print_collection_stats(db["ml_results"], "ML Results")
            return

        # Upload command
        try:
            start = datetime.strptime(args.start_date, "%Y_%m_%d")
            end = (
                datetime.strptime(args.end_date, "%Y_%m_%d") if args.end_date else start
            )
        except ValueError:
            rprint("[red]Invalid date format. Use YYYY_MM_DD.[/red]")
            return

        if start > end:
            rprint("[red]Error: Start date must be before or equal to end date.[/red]")
            return

        success = upload_csv_to_mongodb(args.start_date, args.end_date, db)
        if not success:
            rprint("[red]Upload failed[/red]")
            return

        # Show final collection stats after upload
        _print_collection_stats(db["weather_data"], "Weather Data")

    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user.[/yellow]")
        return
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")
        return


if __name__ == "__main__":
    main()
