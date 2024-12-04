import argparse
from datetime import datetime
from rich import print as rprint
from data_cli_utils import print_banner, connect_to_mongodb
from data_cli_upload import upload_csv_to_mongodb
from data_cli_delete import delete_mongodb_collection
from data_cli_check import check_analysis_results
from data_cli_eda import run_eda_analysis, run_pca_analysis
from data_cli_ml import run_ml_analysis


def main():
    print_banner()
    parser = argparse.ArgumentParser(
        description="Weather data management CLI",
        usage="meteorix [-h] {upload,delete,eda,ml,check} ...",
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
    delete_parser.add_argument('--force', action='store_true', help=argparse.SUPPRESS)

    # EDA command with no arguments
    eda_parser = subparsers.add_parser(
        "eda",
        help="Run exploratory data analysis",
        description="Perform exploratory data analysis including correlation analysis and PCA, then upload results to MongoDB.",
    )
    eda_parser.add_argument('--force', action='store_true', help=argparse.SUPPRESS)

    # ML command with no arguments
    ml_parser = subparsers.add_parser(
        "ml",
        help="Run machine learning analysis",
        description="Execute machine learning models for weather prediction and upload results to MongoDB.",
    )
    ml_parser.add_argument('--force', action='store_true', help=argparse.SUPPRESS)

    # Check command with no arguments
    check_parser = subparsers.add_parser(
        "check",
        help="Check database collections",
        description="Display detailed statistics and content preview for all MongoDB collections.",
    )
    check_parser.add_argument('--force', action='store_true', help=argparse.SUPPRESS)

    args = parser.parse_args()
    db = connect_to_mongodb()

    try:
        if args.command == "check":
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

    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")


if __name__ == "__main__":
    main()
