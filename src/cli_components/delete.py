from rich import print as rprint
from datetime import datetime, timedelta


def delete_mongodb_collection(db, start_date=None, end_date=None):
    """Delete weather data from MongoDB.

    Args:
        db: MongoDB database connection
        start_date (str, optional): Start date in YYYY_MM_DD format
        end_date (str, optional): End date in YYYY_MM_DD format
    """
    collection = db["weather_data"]

    try:
        # Case 1: No dates specified - delete everything
        if not start_date:
            result = collection.delete_many({})
            rprint(
                f"[green]Deleted {result.deleted_count:,} documents from the collection.[/green]"
            )
            return result.acknowledged

        # Parse start date
        start = datetime.strptime(start_date, "%Y_%m_%d")

        # Case 2: Only start date - delete single day
        if not end_date:
            next_day = start + timedelta(days=1)
            query = {"tNow": {"$gte": start, "$lt": next_day}}
            result = collection.delete_many(query)
            rprint(
                f"[green]Deleted {result.deleted_count:,} documents for {start_date}.[/green]"
            )
            return result.acknowledged

        # Case 3: Date range - delete range
        end = datetime.strptime(end_date, "%Y_%m_%d")
        if start > end:
            rprint("[red]Error: Start date must be before or equal to end date.[/red]")
            return False

        # Add one day to end date to include the full end date
        end = end + timedelta(days=1)
        query = {
            "tNow": {
                "$gte": start,
                "$lt": end,  # Changed from $lte to $lt and using end + 1 day
            }
        }
        result = collection.delete_many(query)
        rprint(
            f"[green]Deleted {result.deleted_count:,} documents from {start_date} to {end_date}.[/green]"
        )
        return result.acknowledged

    except ValueError:
        rprint("[red]Invalid date format. Use YYYY_MM_DD.[/red]")
        return False
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")
        return False
