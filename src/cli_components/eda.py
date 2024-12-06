import json
from datetime import datetime, UTC
from rich import print as rprint
from data.data_analysis_eda import main as run_eda
from data.data_analysis_pca import main as run_pca
from data import ANALYSIS_RESULTS_DIR
from .utils import print_collection_stats


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
        results_file = ANALYSIS_RESULTS_DIR / "correlation_data.json"
        with open(results_file, "r") as f:
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
        results_file = ANALYSIS_RESULTS_DIR / "pca_data.json"
        with open(results_file, "r") as f:
            pca_data = json.load(f)

        collection = db["pca_results"]
        collection.delete_many({})
        collection.insert_one(
            {
                "type": "pca_data",
                "data": pca_data,
                "timestamp": datetime.now(UTC),
            }
        )
        print_collection_stats(collection, "PCA Results")

    except FileNotFoundError as e:
        rprint(f"[red]Error: {str(e)}[/red]")
