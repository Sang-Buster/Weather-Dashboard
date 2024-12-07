import json
from datetime import datetime, UTC
from rich import print as rprint
from data.data_analysis_ml import main as run_ml
from src import ANALYSIS_RESULTS_DIR
from .utils import print_collection_stats


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
        plot_file = ANALYSIS_RESULTS_DIR / "ml_plot_data.json"
        with open(plot_file, "r") as f:
            ml_plot_data = json.load(f)

        # Load and upload ML prediction data
        pred_file = ANALYSIS_RESULTS_DIR / "ml_prediction_data.json"
        with open(pred_file, "r") as f:
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
        print_collection_stats(collection, "ML Results")

    except FileNotFoundError as e:
        rprint(f"[red]Error: {str(e)}[/red]")
