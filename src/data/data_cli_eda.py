import json
from datetime import datetime, UTC
from rich import print as rprint
from data_analysis_eda import main as run_eda
from data_analysis_pca import main as run_pca
from data_cli_utils import print_collection_stats


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
        print_collection_stats(collection, "EDA Results")

        # Upload PCA results
        with open("src/data/data_analysis_result/pca_data.json", "r") as f:
            pca_data = json.load(f)
        collection = db["pca_results"]
        collection.delete_many({})
        collection.insert_one(
            {"type": "pca_data", "data": pca_data, "timestamp": datetime.now(UTC)}
        )
        print_collection_stats(collection, "PCA Results")

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
