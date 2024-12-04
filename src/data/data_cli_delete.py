from rich import print as rprint


def delete_mongodb_collection(db):
    """Delete the weather data collection"""
    collection = db["weather_data"]
    result = collection.delete_many({})
    rprint(
        f"[green]Deleted {result.deleted_count:,} documents from the collection.[/green]"
    )
    return result.acknowledged
