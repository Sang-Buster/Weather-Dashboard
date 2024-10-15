import os
import pandas as pd
from pymongo import MongoClient, ASCENDING
from datetime import datetime, timedelta
import argparse
import streamlit as st


def connect_to_mongodb():
    client = MongoClient(st.secrets["mongo_atlas"]["uri"])
    db = client["weather_dashboard"]

    # Check if the collection exists, if not, create it as a time series collection
    if "weather_data" not in db.list_collection_names():
        db.create_collection(
            "weather_data",
            timeseries={
                "timeField": "tNow",
                "metaField": "metadata",
                "granularity": "seconds",
            },
        )

    # Create an index on the time field for better query performance
    db["weather_data"].create_index([("tNow", ASCENDING)])

    return db


def upload_csv_to_mongodb(date, db):
    filename = f"src/data/{date}_weather_station_data.csv"
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return False

    df = pd.read_csv(filename)

    # Convert 'tNow' to datetime
    df["tNow"] = pd.to_datetime(df["tNow"])

    # Log information about the data
    print(f"Loaded {len(df)} entries for {date}")
    print(f"First entry: {df['tNow'].min()}")
    print(f"Last entry: {df['tNow'].max()}")

    records = df.to_dict("records")

    collection = db["weather_data"]

    # Convert date string to datetime object
    date_obj = datetime.strptime(date, "%Y_%m_%d")

    # Clear data for the specific date
    start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    deleted = collection.delete_many(
        {"tNow": {"$gte": start_of_day, "$lt": end_of_day}}
    )
    print(f"Cleared {deleted.deleted_count} existing entries for {date}")

    # Insert new data
    result = collection.insert_many(records)
    print(f"Inserted {len(result.inserted_ids)} entries for {date}")

    return True


def clear_mongodb_collection(db):
    collection = db["weather_data"]
    result = collection.delete_many({})
    print(f"Cleared {result.deleted_count} documents from the collection.")
    return result.acknowledged


def main():
    parser = argparse.ArgumentParser(
        description="Upload or delete weather data from MongoDB"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for the "upload" command
    upload_parser = subparsers.add_parser(
        "upload", help="Upload weather data to MongoDB"
    )
    upload_parser.add_argument("start_date", help="Start date in YYYY_MM_DD format")
    upload_parser.add_argument(
        "end_date", nargs="?", help="End date in YYYY_MM_DD format (optional)"
    )

    # Subparser for the "clear" command
    clear_parser = subparsers.add_parser("clear", help="Clear the MongoDB collection")
    clear_parser.description = "Clear the MongoDB collection. This command does not require any additional arguments."

    args = parser.parse_args()

    db = connect_to_mongodb()

    if args.command == "clear":
        if clear_mongodb_collection(db):
            print("Collection cleared successfully.")
        else:
            print("Failed to clear the collection.")
        return

    # Upload logic
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
