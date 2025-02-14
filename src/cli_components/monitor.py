from datetime import datetime, timedelta
from pathlib import Path
from rich import print as rprint
import glob
from typing import Optional
import json
import os

from src import CSV_DIR

# Store monitor state in a JSON config file within CSV_DIR
MONITOR_CONFIG_FILE = Path(CSV_DIR) / ".monitor_config.json"


def get_monitor_config() -> dict:
    """Read the monitor configuration"""
    default_config = {
        "enabled": True,  # Default to enabled
        "last_check": None,
        "alert_threshold_minutes": 30,
        "check_interval_minutes": 3,
    }

    # Force update existing config with new defaults
    if MONITOR_CONFIG_FILE.exists():
        try:
            with open(MONITOR_CONFIG_FILE, "r") as f:
                current_config = json.load(f)
            # Update with new defaults while preserving current enabled state
            updated_config = default_config.copy()
            updated_config["enabled"] = current_config.get("enabled", True)
            save_monitor_config(updated_config)
            return updated_config
        except Exception:
            # If there's any error, save new defaults
            save_monitor_config(default_config)
            return default_config
    else:
        # If file doesn't exist, create with defaults
        save_monitor_config(default_config)
        return default_config


def save_monitor_config(config: dict) -> None:
    """Save the monitor configuration"""
    try:
        with open(MONITOR_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        rprint(f"[red]Error saving monitor config: {str(e)}[/red]")


def get_latest_data_time() -> Optional[datetime]:
    """Get the timestamp of the most recent data point"""
    try:
        data_dir = Path(CSV_DIR)
        csv_files = glob.glob(str(data_dir / "*_weather_station_data.csv"))

        if not csv_files:
            return None

        # Sort files by name in descending order to check newest first
        sorted_files = sorted(csv_files, reverse=True)

        # Try each file until we find valid data
        for latest_file in sorted_files:
            try:
                with open(latest_file, "rb") as f:
                    # Check if file has content beyond header
                    first_line = f.readline().decode().strip()
                    if first_line == "tNow":  # Header only
                        if len(f.readline().strip()) == 0:  # Empty after header
                            continue  # Try next file

                    # Seek to end to get last line
                    f.seek(-2, os.SEEK_END)
                    while f.read(1) != b"\n":
                        f.seek(-2, os.SEEK_CUR)
                    last_line = f.readline().decode().strip()

                if (
                    not last_line or last_line == "tNow"
                ):  # Skip empty files or header-only files
                    continue

                # Get timestamp from first column
                timestamp_str = last_line.split(",")[0]

                # Try parsing with different formats
                try:
                    # Try with microseconds first
                    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    try:
                        # Try without microseconds
                        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # Handle decimal seconds
                        base_str = timestamp_str.split(".")[0]
                        decimal_str = (
                            timestamp_str.split(".")[1] if "." in timestamp_str else "0"
                        )
                        base_time = datetime.strptime(base_str, "%Y-%m-%d %H:%M:%S")
                        microseconds = int(float("0." + decimal_str) * 1000000)
                        return base_time.replace(microsecond=microseconds)

            except (OSError, IndexError):
                continue  # Try next file if there's an error with current file

        return None  # Return None if no valid data found in any file

    except Exception as e:
        rprint(f"[red]Error checking latest data: {str(e)}[/red]")
        return None


def check_data_freshness() -> tuple[bool, Optional[datetime]]:
    """Check if data is fresh (within threshold)"""
    latest_time = get_latest_data_time()
    config = get_monitor_config()

    if latest_time is None:
        return False, None

    now = datetime.now()
    time_diff = now - latest_time

    return time_diff <= timedelta(
        minutes=config["alert_threshold_minutes"]
    ), latest_time


def show_monitor_status() -> None:
    """Display current monitor status"""
    config = get_monitor_config()
    fresh, latest_time = check_data_freshness()

    rprint(f"\n[bold blue]{'='*60}[/bold blue]")
    rprint("[bold green]Monitor Status[/bold green]")
    rprint(f"[bold blue]{'='*60}[/bold blue]\n")

    status = (
        "[green]enabled[/green]" if config["enabled"] else "[yellow]disabled[/yellow]"
    )
    time_str = latest_time.strftime("%Y-%m-%d %H:%M:%S") if latest_time else "N/A"
    data_state = "[green]fresh[/green]" if fresh else "[red]stale[/red]"

    rprint(f"Monitor state: {status}")
    rprint(f"Data state: {data_state}")
    rprint(f"Alert threshold: {config['alert_threshold_minutes']} minutes")
    rprint(f"Check interval: {config['check_interval_minutes']} minutes")
    rprint(f"Latest data point: {time_str}")

    if latest_time:
        time_diff = datetime.now() - latest_time
        minutes_old = time_diff.total_seconds() / 60
        rprint(f"Data age: {minutes_old:.1f} minutes")


def toggle_monitor(action: str) -> None:
    """Toggle the monitor state or show status"""
    if action not in ["enable", "disable", "status"]:
        rprint("[red]Invalid action. Use 'enable', 'disable', or 'status'[/red]")
        return

    if action == "status":
        show_monitor_status()
        return

    config = get_monitor_config()
    config["enabled"] = action == "enable"
    save_monitor_config(config)

    if config["enabled"]:
        fresh, latest_time = check_data_freshness()
        status = "[green]fresh[/green]" if fresh else "[red]stale[/red]"
        time_str = latest_time.strftime("%Y-%m-%d %H:%M:%S") if latest_time else "N/A"

        rprint("[green]Monitor enabled[/green]")
        rprint(f"Current data status: {status}")
        rprint(f"Latest data point: {time_str}")
    else:
        rprint("[yellow]Monitor disabled[/yellow]")
