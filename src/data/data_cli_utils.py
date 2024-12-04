import colorama
from colorama import Fore, Style
from pymongo import MongoClient
import streamlit as st
from rich import print as rprint
import json
from typing import Any


def print_banner():
    colorama.init()
    lines = [
        "",
        f"{Fore.LIGHTBLUE_EX}███╗░░░███╗███████╗████████╗███████╗░█████╗░██████╗░██╗██╗░░██╗",
        f"{Fore.LIGHTBLUE_EX}████╗░████║██╔════╝╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██║╚██╗██╔╝",
        f"{Fore.LIGHTBLUE_EX}██╔████╔██║█████╗░░░░░██║░░░█████╗░░██║░░██║██████╔╝██║░╚███╔╝░",
        f"{Fore.LIGHTBLUE_EX}██║╚██╔╝██║██╔══╝░░░░░██║░░░██╔══╝░░██║░░██║██╔══██╗██║░██╔██╗░",
        f"{Fore.LIGHTBLUE_EX}██║░╚═╝░██║███████╗░░░██║░░░███████╗╚█████╔╝██║░░██║██║██╔╝╚██╗",
        f"{Fore.LIGHTBLUE_EX}╚═╝░░░░░╚═╝╚══════╝░░░╚═╝░░░╚══════╝░╚════╝░╚═╝░░╚═╝╚═╝╚═╝░░╚═╝",
        f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}---------------------------------------------------------------",
        f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}      °•☁︎ Meteorix: A Weather Station Management CLI °•☁︎",
        f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}---------------------------------------------------------------{Style.RESET_ALL}",
        "",
    ]

    for line in lines:
        print(line)


def connect_to_mongodb() -> Any:
    """Establish MongoDB connection and initialize time series collection."""
    client = MongoClient(
        st.secrets["mongo"]["uri"],
        maxPoolSize=100,
        minPoolSize=20,
        maxIdleTimeMS=45000,
        connectTimeoutMS=2000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=5000,
        retryWrites=True,
        retryReads=True,
        compressors=["zstd"],
        maxConnecting=8,
        w="majority",
        readPreference="secondaryPreferred",
    )
    db = client["weather_dashboard"]

    if "weather_data" not in db.list_collection_names():
        print("Creating time series collection...")
        db.create_collection(
            "weather_data", timeseries={"timeField": "tNow", "granularity": "seconds"}
        )

    db["weather_data"].create_index([("tNow", 1)])
    return db


def print_collection_stats(collection: Any, collection_name: str) -> None:
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


def print_usage(usage_text):
    print(f"{Fore.YELLOW}Usage:{Style.RESET_ALL} {usage_text}\n")
