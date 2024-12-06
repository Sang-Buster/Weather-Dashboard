import os
import sys
import argparse
from datetime import datetime
from rich import print as rprint

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.data.data_cli_utils import print_banner, connect_to_mongodb  # noqa: E402
from src.data.data_cli_upload import upload_csv_to_mongodb  # noqa: E402
from src.data.data_cli_delete import delete_mongodb_collection  # noqa: E402
from src.data.data_cli_check import check_analysis_results  # noqa: E402
from src.data.data_cli_eda import run_eda_analysis, run_pca_analysis  # noqa: E402
from src.data.data_cli_ml import run_ml_analysis  # noqa: E402
from src.data.data_cli_info import get_available_date_range  # noqa: E402
from src.data.data_cli_who import show_who_info  # noqa: E402
from src.data.data_cli_head import show_head  # noqa: E402
from src.data.data_cli_tail import show_tail  # noqa: E402


def main():
    print_banner()
    parser = argparse.ArgumentParser(
        description="Weather data management CLI",
        usage="meteorix [-h] {upload,delete,eda,ml,check,info,who,head,tail} ...",
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
    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete all weather data",
        description="Remove all weather data records from the MongoDB collection.",
    )
    delete_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # EDA command with no arguments
    eda_parser = subparsers.add_parser(
        "eda",
        help="Run exploratory data analysis",
        description="Perform exploratory data analysis including correlation analysis and PCA, then upload results to MongoDB.",
    )
    eda_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # ML command with no arguments
    ml_parser = subparsers.add_parser(
        "ml",
        help="Run machine learning analysis",
        description="Execute machine learning models for weather prediction and upload results to MongoDB.",
    )
    ml_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # Check command with no arguments
    check_parser = subparsers.add_parser(
        "check",
        help="Check database collections",
        description="Display detailed statistics and content preview for all MongoDB collections.",
    )
    check_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # Info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show available date range",
        description="Display the date range of available weather station data files and identify any missing dates.",
    )
    info_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # Who command
    who_parser = subparsers.add_parser(
        "who",
        help="Show information about the bot and its creators",
        description="Display detailed information about the Meteorix bot and its creators.",
    )
    who_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # Head command with updated help
    head_parser = subparsers.add_parser(
        "head",
        help="Show earliest logged timestamp or first 5 rows if date specified",
        description="""Without a date: Shows the earliest timestamp in the dataset.
With a date (YYYY_MM_DD format): Shows the first 5 rows of that specific date.""",
    )
    head_parser.add_argument(
        "date", nargs="?", help="Optional: Date to show first 5 rows for (YYYY_MM_DD)"
    )

    # Tail command with updated help
    tail_parser = subparsers.add_parser(
        "tail",
        help="Show latest logged timestamp or last 5 rows if date specified",
        description="""Without a date: Shows the latest timestamp in the dataset.
With a date (YYYY_MM_DD format): Shows the last 5 rows of that specific date.""",
    )
    tail_parser.add_argument(
        "date", nargs="?", help="Optional: Date to show last 5 rows for (YYYY_MM_DD)"
    )

    args = parser.parse_args()
    db = connect_to_mongodb()

    try:
        if args.command == "who":
            show_who_info()
        elif args.command == "check":
            check_analysis_results(db)
        elif args.command == "delete":
            if delete_mongodb_collection(db):
                rprint("[green]Collection deleted successfully.[/green]")
            else:
                rprint("[red]Failed to delete collection.[/red]")
        elif args.command == "eda":
            run_eda_analysis(db)
            run_pca_analysis(db)
        elif args.command == "ml":
            run_ml_analysis(db)
        elif args.command == "upload":
            try:
                start = datetime.strptime(args.start_date, "%Y_%m_%d")
                end = (
                    datetime.strptime(args.end_date, "%Y_%m_%d")
                    if args.end_date
                    else start
                )
                if start > end:
                    rprint(
                        "[red]Error: Start date must be before or equal to end date.[/red]"
                    )
                    return
                success = upload_csv_to_mongodb(args.start_date, args.end_date, db)
                if not success:
                    rprint("[red]Upload failed[/red]")
            except ValueError:
                rprint("[red]Invalid date format. Use YYYY_MM_DD.[/red]")
        elif args.command == "info":
            get_available_date_range()
        elif args.command == "head":
            show_head(args.date if hasattr(args, "date") else None)
        elif args.command == "tail":
            show_tail(args.date if hasattr(args, "date") else None)

    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")


if __name__ == "__main__":
    main()
