import os
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import argparse
import streamlit as st
import json
from data_analysis_eda import main as run_eda
from data_analysis_pca import main as run_pca
from data_analysis_ml import main as run_ml
from typing import Any
import subprocess

# Constants
COLLECTIONS_CONFIG = {
    "weather_data": {
        "timeseries": {
            "timeField": "tNow",
            "metaField": "metadata",
            "granularity": "seconds",
        }
    },
    "eda_results": {},
    "pca_results": {},
    "ml_results": {},
}

BATCH_SIZE = 10000
DATA_DIR = "src/data"


def connect_to_mongodb() -> Any:
    """Establish MongoDB connection and initialize collections."""
    client = MongoClient(st.secrets["mongo"]["uri"])
    db = client["weather_dashboard"]

    # Initialize collections
    for collection_name, settings in COLLECTIONS_CONFIG.items():
        if collection_name not in db.list_collection_names():
            db.create_collection(
                collection_name, **settings
            ) if settings else db.create_collection(collection_name)

    return db


def _print_collection_stats(collection: Any, collection_name: str) -> None:
    """Helper function to print collection statistics and preview."""
    total_docs = collection.count_documents({})
    print(f"\n{collection_name} Collection Stats:")
    print(f"Total Records: {total_docs:,}")

    # Show preview of first 3 documents
    if total_docs > 0:
        print("\nFirst 3 documents preview:")
        for doc in collection.find({}, {"_id": 0}).limit(3):
            print(json.dumps(doc, indent=2, default=str))


def download_data(db: Any) -> None:
    """Download collections using mongoexport with optimized settings."""
    os.makedirs(DATA_DIR, exist_ok=True)

    uri = st.secrets["mongo"]["uri"]

    for collection_name in COLLECTIONS_CONFIG.keys():
        if collection_name not in db.list_collection_names():
            continue

        collection = db[collection_name]
        total_docs = collection.count_documents({})

        # Print collection stats and preview
        _print_collection_stats(collection, collection_name)

        if total_docs == 0:
            print(f"Skipping download of empty collection: {collection_name}")
            continue

        print(f"\nDownloading {collection_name}...")
        csv_path = os.path.join(DATA_DIR, f"{collection_name}.csv")

        # Get field names from first document for CSV headers
        first_doc = collection.find_one({}, {"_id": 0})
        fields = ",".join(first_doc.keys()) if first_doc else "*"

        # Use mongoexport command with optimized settings
        cmd = [
            "mongoexport",
            f"--uri={uri}",
            "--db=weather_dashboard",
            f"--collection={collection_name}",
            f"--out={csv_path}",
            "--type=csv",
            f"--fields={fields}",
            "--quiet",  # Reduce output noise
            "--readPreference=nearest",  # Optimize read performance
            "--sort={tNow: 1}",  # Sort by timestamp
        ]

        try:
            # Export directly to CSV
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            # Print success message with record count
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                print(f"Downloaded {len(df):,} records to {csv_path}")
            else:
                print(f"Error: Failed to create {csv_path}")
                if result.stderr:
                    print(f"Error details: {result.stderr}")

        except subprocess.CalledProcessError as e:
            print(f"Error exporting {collection_name}: {e.stderr}")
            # Print the full command for debugging (hide URI)
            debug_cmd = " ".join(
                [c if not c.startswith("--uri=") else "--uri=<hidden>" for c in cmd]
            )
            print(f"Failed command: {debug_cmd}")
        except Exception as e:
            print(f"Error processing {collection_name}: {str(e)}")


def run_eda_analysis(db):
    """Run EDA analysis and upload results"""
    # Run analysis
    run_eda()  # This creates correlation_data.json

    # Load and upload correlation data
    try:
        with open("src/data/correlation_data.json", "r") as f:
            correlation_data = json.load(f)

        # Clear existing results and insert new ones
        collection = db["eda_results"]
        collection.delete_many({})
        collection.insert_one(
            {
                "correlation_data": correlation_data,
                "timestamp": datetime.now().isoformat(),
            }
        )
        print("EDA results uploaded to MongoDB")
    except FileNotFoundError:
        print("Error: correlation_data.json not found")


def run_pca_analysis(db):
    """Run PCA analysis and upload results"""
    # Run PCA analysis
    run_pca()  # This creates pca_data.json

    # Load and upload PCA data
    try:
        with open("src/data/pca_data.json", "r") as f:
            pca_data = json.load(f)

        # Clear existing results and insert new ones
        collection = db["pca_results"]
        collection.delete_many({})
        collection.insert_one(
            {"pca_data": pca_data, "timestamp": datetime.now().isoformat()}
        )
        print("PCA results uploaded to MongoDB")
    except FileNotFoundError:
        print("Error: pca_data.json not found")


def run_ml_analysis(db):
    """Run ML analysis and upload results"""
    # Run ML analysis
    run_ml()  # This creates ml_plot_data.json

    # Load and upload ML data
    try:
        with open("src/data/ml_plot_data.json", "r") as f:
            ml_data = json.load(f)

        # Clear existing results and insert new ones
        collection = db["ml_results"]
        collection.delete_many({})
        collection.insert_one(
            {"ml_data": ml_data, "timestamp": datetime.now().isoformat()}
        )
        print("ML results uploaded to MongoDB")
    except FileNotFoundError:
        print("Error: ml_plot_data.json not found")


def upload_csv_to_mongodb(date: str, db: Any) -> bool:
    """Upload CSV data to MongoDB for a specific date."""
    filename = os.path.join(DATA_DIR, f"{date}_weather_station_data.csv")
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return False

    try:
        df = pd.read_csv(filename)
        df["tNow"] = pd.to_datetime(df["tNow"])

        print(f"Loaded {len(df)} entries for {date}")
        print(f"Time range: {df['tNow'].min()} to {df['tNow'].max()}")

        collection = db["weather_data"]
        date_obj = datetime.strptime(date, "%Y_%m_%d")

        # Clear existing data
        start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        deleted = collection.delete_many(
            {"tNow": {"$gte": start_of_day, "$lt": end_of_day}}
        )
        print(f"Cleared {deleted.deleted_count} existing entries for {date}")

        # Insert new data
        result = collection.insert_many(df.to_dict("records"))
        print(f"Inserted {len(result.inserted_ids)} entries for {date}")
        return True

    except Exception as e:
        print(f"Error uploading data for {date}: {str(e)}")
        return False


def delete_mongodb_collection(db):
    """Delete the weather data collection"""
    collection = db["weather_data"]
    result = collection.delete_many({})
    print(f"Deleted {result.deleted_count} documents from the collection.")
    return result.acknowledged


def main():
    parser = argparse.ArgumentParser(description="Weather data management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Upload command
    upload_parser = subparsers.add_parser(
        "upload", help="Upload weather data to MongoDB"
    )
    upload_parser.add_argument("start_date", help="Start date in YYYY_MM_DD format")
    upload_parser.add_argument(
        "end_date", nargs="?", help="End date in YYYY_MM_DD format (optional)"
    )

    # Delete command
    delete_parser = subparsers.add_parser(
        "delete", help="Delete the weather data collection"
    )
    delete_parser.description = "Delete the MongoDB collection. This command does not require any additional arguments."

    # EDA command
    eda_parser = subparsers.add_parser(
        "eda", help="Run EDA and PCA analysis and upload results to MongoDB"
    )
    eda_parser.description = "Performs exploratory data analysis and PCA, uploads results to eda_results collection"

    # ML command
    ml_parser = subparsers.add_parser(
        "ml", help="Run ML analysis and upload results to MongoDB"
    )
    ml_parser.description = "Performs machine learning analysis and uploads results to ml_results collection"

    args = parser.parse_args()
    db = connect_to_mongodb()

    if args.command == "delete":
        if delete_mongodb_collection(db):
            print("Collection deleted successfully.")
        else:
            print("Failed to delete the collection.")
        return

    elif args.command == "eda":
        run_eda_analysis(db)
        run_pca_analysis(db)
        return

    elif args.command == "ml":
        run_ml_analysis(db)
        return

    # Upload logic (existing code)
    try:
        start = datetime.strptime(args.start_date, "%Y_%m_%d")
        end = datetime.strptime(args.end_date, "%Y_%m_%d") if args.end_date else start
    except ValueError:
        print("Invalid date format. Use YYYY_MM_DD.")
        return

    if start > end:
        print("Error: Start date must be before or equal to end date.")
        return

    current_date = start
    while current_date <= end:
        date_str = current_date.strftime("%Y_%m_%d")
        success = upload_csv_to_mongodb(date_str, db)
        if not success:
            print(f"Failed to upload data for {date_str}")
        current_date += timedelta(days=1)

    print("Upload complete.")


if __name__ == "__main__":
    main()
