from cli_components import (
    check_analysis_results,
    delete_mongodb_collection,
    run_eda_analysis,
    run_ml_analysis,
    get_available_date_range,
    show_who_info,
    show_head,
    show_tail,
    upload_csv_to_mongodb,
    print_banner,
    connect_to_mongodb,
    spit_csv_data,
)

import sys
import argparse
from datetime import datetime
from rich import print as rprint

from src import SRC_DIR

# Add project root to Python path
sys.path.insert(0, str(SRC_DIR))


def main():
    # Only print banner if not using spit command
    if len(sys.argv) > 1 and sys.argv[1] != "spit":
        print_banner()

    parser = argparse.ArgumentParser(
        description="Weather data management CLI",
        usage="meteorix [-h] {upload,delete,check,head,tail,info,spit,eda,ml,who,help} ...",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Define subparsers in the desired order
    # 1. Upload command
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload weather data to MongoDB",
        description="Upload weather station data from CSV files to MongoDB.",
    )
    upload_parser.add_argument("start_date", help="Start date (YYYY_MM_DD)")
    upload_parser.add_argument(
        "end_date", nargs="?", help="End date (YYYY_MM_DD, optional)"
    )

    # 2. Delete command
    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete all weather data from MongoDB",
        description="Remove all weather data records from the MongoDB collection.",
    )
    delete_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # 3. Check command
    check_parser = subparsers.add_parser(
        "check",
        help="Check database collections",
        description="Display detailed statistics and content preview for all MongoDB collections.",
    )
    check_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # 4. Head command
    head_parser = subparsers.add_parser(
        "head",
        help="Show earliest logged timestamp or first 5 rows if date specified",
        description="""Without a date: Shows the earliest timestamp in the dataset.
With a date (YYYY_MM_DD format): Shows the first 5 rows of that specific date.""",
    )
    head_parser.add_argument(
        "date", nargs="?", help="Optional: Date to show first 5 rows for (YYYY_MM_DD)"
    )

    # 5. Tail command
    tail_parser = subparsers.add_parser(
        "tail",
        help="Show latest logged timestamp or last 5 rows if date specified",
        description="""Without a date: Shows the latest timestamp in the dataset.
With a date (YYYY_MM_DD format): Shows the last 5 rows of that specific date.""",
    )
    tail_parser.add_argument(
        "date", nargs="?", help="Optional: Date to show last 5 rows for (YYYY_MM_DD)"
    )

    # 6. Info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show available date range and file statistics",
        description="Display available date range, file details including row counts and sizes, and identify any missing dates in the sequence. Optionally filter by month.",
    )
    info_parser.add_argument(
        "month",
        nargs="?",
        help="Optional: Month to show statistics for (YYYY_MM)",
    )
    info_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # 7. Spit command
    spit_parser = subparsers.add_parser(
        "spit",
        help="Get raw CSV data for specified dates",
        description="Retrieve and output raw CSV data for a specific date or date range.",
    )
    spit_parser.add_argument("start_date", help="Start date (YYYY_MM_DD)")
    spit_parser.add_argument(
        "end_date", nargs="?", help="End date (YYYY_MM_DD, optional)"
    )

    # 8. EDA command
    eda_parser = subparsers.add_parser(
        "eda",
        help="Run exploratory data analysis",
        description="Perform exploratory data analysis including correlation analysis and PCA, then upload results to MongoDB.",
    )
    eda_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # 9. ML command
    ml_parser = subparsers.add_parser(
        "ml",
        help="Run machine learning analysis",
        description="Execute machine learning models for weather prediction and upload results to MongoDB.",
    )
    ml_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

    # 10. Who command
    who_parser = subparsers.add_parser(
        "who",
        help="Show information about the bot",
        description="Display detailed information about the Meteorix bot and its creators.",
    )
    who_parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)

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
            get_available_date_range(args.month if hasattr(args, "month") else None)
        elif args.command == "head":
            show_head(args.date if hasattr(args, "date") else None)
        elif args.command == "tail":
            show_tail(args.date if hasattr(args, "date") else None)
        elif args.command == "spit":
            try:
                start = datetime.strptime(args.start_date, "%Y_%m_%d")
                end = (
                    datetime.strptime(args.end_date, "%Y_%m_%d")
                    if args.end_date
                    else start
                )
                if start > end:
                    sys.stderr.write(
                        "[red]Error: Start date must be before or equal to end date.[/red]\n"
                    )
                    return
                filename, csv_buffer = spit_csv_data(args.start_date, args.end_date)
                # Print only the CSV data, no extra output
                sys.stdout.write(csv_buffer.getvalue())
            except ValueError:
                sys.stderr.write("[red]Invalid date format. Use YYYY_MM_DD.[/red]\n")

    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")


if __name__ == "__main__":
    main()
