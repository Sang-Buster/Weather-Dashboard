import argparse
import asyncio
import sys
from datetime import datetime

import streamlit as st
from rich import print as rprint

from cli_components import (
    check_analysis_results,
    connect_to_mongodb,
    create_weather_plot,
    delete_mongodb_collection,
    get_available_date_range,
    get_pi_ip,
    get_system_stats,
    handle_chat_command,
    print_banner,
    run_eda_analysis,
    run_ml_analysis,
    set_frequency,
    show_head,
    show_tail,
    show_who_info,
    spit_csv_data,
    toggle_monitor,
    upload_csv_to_mongodb,
)
from src import SRC_DIR

# Add project root to Python path
sys.path.insert(0, str(SRC_DIR))


def get_parser():
    parser = argparse.ArgumentParser(
        description="Weather data management CLI",
        usage="meteorix [-h] {upload, delete, check, head, tail, info, spit, plot, monitor, freq, ifconfig, top, chat, eda, ml, who}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command configurations
    commands = {
        "upload": {
            "help": "Upload weather data to MongoDB",
            "description": "Upload weather station data from CSV files to MongoDB. If no dates specified, uploads the last 3 days.",
            "args": [
                (
                    "start_date",
                    {
                        "nargs": "?",
                        "help": "Start date (YYYY_MM_DD, optional). If only start_date is provided, it will upload just that single day",
                    },
                ),
                (
                    "end_date",
                    {
                        "nargs": "?",
                        "help": "End date (YYYY_MM_DD, optional). Required only if uploading a date range",
                    },
                ),
            ],
        },
        "delete": {
            "help": "Delete weather data from MongoDB",
            "description": "Remove weather data records from MongoDB. Without dates: deletes all data. With start_date: deletes that day. With both dates: deletes date range.",
            "args": [
                (
                    "start_date",
                    {
                        "nargs": "?",
                        "help": "Start date (YYYY_MM_DD, optional). If only start_date provided, deletes just that single day",
                    },
                ),
                (
                    "end_date",
                    {
                        "nargs": "?",
                        "help": "End date (YYYY_MM_DD, optional). Required only if deleting a date range",
                    },
                ),
            ],
        },
        "check": {
            "help": "Check database collections",
            "description": "Display detailed statistics and content preview for all MongoDB collections.",
            "args": [("--force", {"action": "store_true", "help": argparse.SUPPRESS})],
        },
        "head": {
            "help": "Show earliest logged timestamp or first 5 rows if date specified",
            "description": """Without a date: Shows the earliest timestamp in the dataset.
With a date (YYYY_MM_DD format): Shows the first 5 rows of that specific date.""",
            "args": [
                (
                    "date",
                    {
                        "nargs": "?",
                        "help": "Optional: Date to show first 5 rows for (YYYY_MM_DD)",
                    },
                )
            ],
        },
        "tail": {
            "help": "Show latest logged timestamp or last 5 rows if date specified",
            "description": """Without a date: Shows the latest timestamp in the dataset.
With a date (YYYY_MM_DD format): Shows the last 5 rows of that specific date.""",
            "args": [
                (
                    "date",
                    {
                        "nargs": "?",
                        "help": "Optional: Date to show last 5 rows for (YYYY_MM_DD)",
                    },
                )
            ],
        },
        "info": {
            "help": "Show available date range and file statistics",
            "description": "Display available date range, file details including row counts and sizes, and identify any missing dates in the sequence. Optionally filter by month.",
            "args": [
                (
                    "month",
                    {
                        "nargs": "?",
                        "help": "Optional: Month to show statistics for (YYYY_MM)",
                    },
                ),
                ("--force", {"action": "store_true", "help": argparse.SUPPRESS}),
            ],
        },
        "spit": {
            "help": "Get raw CSV data for specified dates",
            "description": "Retrieve and output raw CSV data for a specific date or date range.",
            "args": [
                ("start_date", {"help": "Start date (YYYY_MM_DD)"}),
                ("end_date", {"nargs": "?", "help": "End date (YYYY_MM_DD, optional)"}),
            ],
        },
        "plot": {
            "help": "Create weather data plots",
            "description": "Generate plots of weather data for a specific date or date range.",
            "args": [
                ("start_date", {"help": "Start date (YYYY_MM_DD)"}),
                ("end_date", {"nargs": "?", "help": "End date (YYYY_MM_DD, optional)"}),
            ],
        },
        "monitor": {
            "help": "Enable/disable/check data collection monitoring",
            "description": "Monitor data collection status and send alerts if data is stale",
            "args": [
                (
                    "action",
                    {
                        "choices": ["enable", "disable", "status"],
                        "help": "Enable, disable, or check monitoring status",
                    },
                ),
            ],
        },
        "freq": {
            "help": "Control data logging frequency",
            "description": "Set or check the data logging frequency on the Raspberry Pi. Use '0' for low frequency (1Hz), '1' for high frequency (32Hz), or 'status' to check current mode.",
            "args": [
                (
                    "action",
                    {
                        "choices": ["0", "1", "status"],
                        "help": "0 (1Hz), 1 (32Hz), or status",
                    },
                ),
            ],
        },
        "ifconfig": {
            "help": "Show Raspberry Pi network information",
            "description": "Display network interface information from the weather station Raspberry Pi.",
            "args": [],
        },
        "top": {
            "help": "Show Raspberry Pi system status",
            "description": "Display system metrics including CPU, memory, disk usage and temperature.",
            "args": [],
        },
        "chat": {
            "help": "Chat with an LLM about weather data",
            "description": f"""
Chat with an AI assistant about weather data and analysis.

Examples:
  meteorix chat models                    List available AI models
  meteorix chat "What's the temperature?"  Chat using default model
  meteorix chat --model {st.secrets["ollama"]["model"]} "Analyze wind patterns"

The assistant has access to recent weather data and can:
• Analyze weather patterns and trends
• Answer questions about current conditions
• Provide insights about the data
• Compare data across different time periods
""",
            "args": [
                (
                    "--model",
                    {
                        "default": st.secrets["ollama"]["model"],
                        "metavar": "MODEL_NAME",
                        "help": f"AI model to use (default: {st.secrets['ollama']['model']})",
                    },
                ),
                (
                    "action_or_prompt",
                    {
                        "nargs": "?",
                        "metavar": "PROMPT|'models'",
                        "help": "Your question/prompt, or 'models' to list available AI models",
                    },
                ),
                (
                    "remaining_prompt",
                    {
                        "nargs": "*",
                        "help": argparse.SUPPRESS,  # Hide from help message
                    },
                ),
            ],
            "epilog": "Use 'meteorix chat models' to see available AI models",
        },
        "eda": {
            "help": "Run exploratory data analysis",
            "description": "Perform exploratory data analysis including correlation analysis and PCA, then upload results to MongoDB.",
            "args": [("--force", {"action": "store_true", "help": argparse.SUPPRESS})],
        },
        "ml": {
            "help": "Run machine learning analysis",
            "description": "Execute machine learning models for weather prediction and upload results to MongoDB.",
            "args": [("--force", {"action": "store_true", "help": argparse.SUPPRESS})],
        },
        "who": {
            "help": "Show information about the bot",
            "description": "Display detailed information about the Meteorix bot and its creators.",
            "args": [("--force", {"action": "store_true", "help": argparse.SUPPRESS})],
        },
    }

    # Create subparsers from command configurations
    for cmd, config in commands.items():
        parser_obj = subparsers.add_parser(
            cmd,
            help=config["help"],
            description=config.get("description"),
            epilog=config.get("epilog"),
            formatter_class=argparse.RawDescriptionHelpFormatter,  # Preserve formatting
        )
        for arg_name, arg_config in config["args"]:
            parser_obj.add_argument(arg_name, **arg_config)

    return parser


async def async_main():
    """Async main function for commands that need async support."""
    # Only print banner if not using spit or plot command
    if len(sys.argv) > 1 and sys.argv[1] not in ["spit"]:
        print_banner()

    parser = get_parser()
    args = parser.parse_args()
    db = connect_to_mongodb()

    # Separate async and non-async command handlers
    async_handlers = {
        "chat": lambda: handle_chat_command(args),
        # Add other async commands here if needed
    }

    regular_handlers = {
        "who": lambda: show_who_info(),
        "check": lambda: check_analysis_results(db),
        "delete": lambda: delete_mongodb_collection(
            db,
            args.start_date if hasattr(args, "start_date") else None,
            args.end_date if hasattr(args, "end_date") else None,
        ),
        "eda": lambda: run_eda_analysis(db),
        "ml": lambda: run_ml_analysis(db),
        "info": lambda: get_available_date_range(
            args.month if hasattr(args, "month") else None
        ),
        "head": lambda: show_head(args.date if hasattr(args, "date") else None),
        "tail": lambda: show_tail(args.date if hasattr(args, "date") else None),
        "monitor": lambda: toggle_monitor(args.action),
        "ifconfig": lambda: get_pi_ip(),
        "top": lambda: get_system_stats(),
        "freq": lambda: handle_freq_command(args),
    }

    # Date-based command handlers
    date_handlers = {
        "upload": lambda start, end: upload_csv_to_mongodb(start, end, db),
        "spit": lambda start, end: sys.stdout.write(
            spit_csv_data(start, end)[1].getvalue()
        ),
        "plot": lambda start, end: handle_plot_command(start, end, save_locally=True),
    }

    try:
        if args.command in async_handlers:
            # Handle async commands
            result = async_handlers[args.command]()
            if result is not None:  # Only await if we got a coroutine
                await result
        elif args.command in regular_handlers:
            # Handle regular synchronous commands
            regular_handlers[args.command]()
        elif args.command in date_handlers:
            # Handle date-based commands
            handle_date_command(args, date_handlers[args.command])
    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")


def handle_date_command(args, handler):
    """Handle commands that require date processing."""
    try:
        # If no dates provided, just call the handler
        if not args.start_date:
            handler(None, None)
            return

        # Parse start date if provided
        start = datetime.strptime(args.start_date, "%Y_%m_%d")

        # Parse end date if provided, otherwise use start date
        if args.end_date:
            end = datetime.strptime(args.end_date, "%Y_%m_%d")
            if start > end:
                rprint(
                    "[red]Error: Start date must be before or equal to end date.[/red]"
                )
                return
            handler(args.start_date, args.end_date)
        else:
            # Only start date provided
            handler(args.start_date, None)

    except ValueError:
        rprint("[red]Invalid date format. Use YYYY_MM_DD.[/red]")


def handle_plot_command(start_date, end_date, save_locally=True):
    """Handle plot command specifically."""
    try:
        filenames, buffers, filepaths = create_weather_plot(
            start_date, end_date, save_locally=save_locally
        )

        if save_locally:
            for filepath in filepaths:
                rprint(f"[green]Plot saved as: {filepath}[/green]")
    except Exception as e:
        rprint(f"[red]Error creating plot: {str(e)}[/red]")


def handle_freq_command(args):
    """Handle frequency control command."""
    set_frequency(None if args.action == "status" else args.action)


def main():
    """Main entry point that handles both async and sync commands."""
    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        # Run async main for chat command
        asyncio.run(async_main())
    else:
        # Run sync main for other commands
        if len(sys.argv) > 1 and sys.argv[1] not in ["spit"]:
            print_banner()

        parser = get_parser()
        args = parser.parse_args()
        db = connect_to_mongodb()

        try:
            # Handle regular commands
            if args.command == "chat":
                rprint("[red]Error: Chat command must be run with async support[/red]")
                return

            handlers = {
                "who": lambda: show_who_info(),
                "check": lambda: check_analysis_results(db),
                "delete": lambda: delete_mongodb_collection(
                    db,
                    args.start_date if hasattr(args, "start_date") else None,
                    args.end_date if hasattr(args, "end_date") else None,
                ),
                "eda": lambda: run_eda_analysis(db),
                "ml": lambda: run_ml_analysis(db),
                "info": lambda: get_available_date_range(
                    args.month if hasattr(args, "month") else None
                ),
                "head": lambda: show_head(args.date if hasattr(args, "date") else None),
                "tail": lambda: show_tail(args.date if hasattr(args, "date") else None),
                "monitor": lambda: toggle_monitor(args.action),
                "ifconfig": lambda: get_pi_ip(),
                "top": lambda: get_system_stats(),
                "freq": lambda: handle_freq_command(args),
            }

            date_handlers = {
                "upload": lambda start, end: upload_csv_to_mongodb(start, end, db),
                "spit": lambda start, end: sys.stdout.write(
                    spit_csv_data(start, end)[1].getvalue()
                ),
                "plot": lambda start, end: handle_plot_command(
                    start, end, save_locally=True
                ),
            }

            if args.command in handlers:
                handlers[args.command]()
            elif args.command in date_handlers:
                handle_date_command(args, date_handlers[args.command])
        except KeyboardInterrupt:
            rprint("\n[yellow]Operation cancelled by user.[/yellow]")
        except Exception as e:
            rprint(f"[red]Error: {str(e)}[/red]")


if __name__ == "__main__":
    main()
