from rich import print as rprint
from .ifconfig import SSHClient, find_pi_address
from datetime import datetime


def set_frequency(freq=None):
    """Set or check the data logging frequency on the Raspberry Pi

    Args:
        freq (str, optional): '1' for high frequency (32Hz), '0' for low frequency (1Hz)
    """
    try:
        # Find the Pi's current address
        pi_address = find_pi_address()
        if not pi_address:
            raise Exception("Could not locate the Raspberry Pi on the network")

        # Get SSH client instance for status check
        ssh = SSHClient.get_instance().get_client(pi_address)

        def check_current_frequency():
            """Helper function to check current frequency mode"""
            stdin, stdout, stderr = ssh.exec_command(f"tail -n 10 {latest_file}")
            lines = stdout.readlines()

            timestamps = []
            for line in lines:
                try:
                    timestamp_str = line.strip().split(",")[0]
                    if timestamp_str != "tNow":  # Skip header if present
                        # Parse timestamp with microseconds
                        try:
                            timestamp = datetime.strptime(
                                timestamp_str, "%Y-%m-%d %H:%M:%S.%f"
                            )
                        except ValueError:
                            # If no microseconds, try without
                            timestamp = datetime.strptime(
                                timestamp_str, "%Y-%m-%d %H:%M:%S"
                            )
                        timestamps.append(timestamp)
                except (ValueError, IndexError):
                    continue

            if len(timestamps) >= 2:
                # Calculate time differences in microseconds for more precise measurement
                time_diffs = [
                    (timestamps[i + 1] - timestamps[i]).total_seconds()
                    for i in range(len(timestamps) - 1)
                ]
                if time_diffs:  # Make sure we have differences to analyze
                    avg_interval = sum(time_diffs) / len(time_diffs)
                    # Consider it high frequency if average interval is less than 0.1 seconds
                    return avg_interval < 0.1, avg_interval
            return False, 1.0  # Return default 1-second interval when can't determine

        # If no frequency specified, check current status
        if freq is None:
            # Check if the Weather Station logger is running
            stdin, stdout, stderr = ssh.exec_command("sudo screen -ls | grep logger")
            screen_output = stdout.read().decode().strip()

            if not screen_output:
                rprint("[yellow]Weather Station logger is not running[/yellow]")
                return

            # Check for active data files
            stdin, stdout, stderr = ssh.exec_command(
                "ls -t /var/tmp/wx/*_weather_station_data.csv 2>/dev/null | head -1"
            )
            latest_file = stdout.read().decode().strip()

            if not latest_file:
                rprint("[yellow]No active data files found[/yellow]")
                return

            # Get file's last modification time
            stdin, stdout, stderr = ssh.exec_command(f"stat -c %Y {latest_file}")
            file_time = int(stdout.read().decode().strip())
            current_time = int(ssh.exec_command("date +%s")[1].read().decode().strip())

            is_high_freq, avg_interval = check_current_frequency()

            # Display current status
            if current_time - file_time < 5:  # File was modified in last 5 seconds
                if is_high_freq:
                    rprint(
                        "[green]Currently running in HIGH frequency mode (32 Hz)[/green]"
                    )
                    rprint(
                        f"[yellow]High frequency data being logged to: {latest_file}[/yellow]"
                    )
                    rprint(
                        f"[blue]Average interval between readings: {avg_interval:.3f} seconds[/blue]"
                    )
                else:
                    rprint(
                        "[green]Currently running in LOW frequency mode (1 Hz)[/green]"
                    )
                    rprint(f"[yellow]Data being logged to: {latest_file}[/yellow]")
                    if avg_interval:  # Only show interval if we could calculate it
                        rprint(
                            f"[blue]Average interval between readings: {avg_interval:.3f} seconds[/blue]"
                        )
            else:
                rprint(
                    "[yellow]Warning: Data collection appears to be stalled[/yellow]"
                )
                rprint(
                    f"[yellow]Last file modification was {current_time - file_time} seconds ago[/yellow]"
                )
            return

        # Validate frequency input
        if freq not in ["0", "1"]:
            raise ValueError("Frequency must be '1' (32Hz) or '0' (1Hz)")

        # Get current frequency before making changes
        stdin, stdout, stderr = ssh.exec_command(
            "ls -t /var/tmp/wx/*_weather_station_data.csv 2>/dev/null | head -1"
        )
        latest_file = stdout.read().decode().strip()
        current_high_freq, _ = check_current_frequency()

        try:
            if freq == "1":
                if current_high_freq:
                    rprint("[yellow]Already running in HIGH frequency mode[/yellow]")
                    return True
                rprint("[yellow]Starting HIGH frequency logging...[/yellow]")
                ssh.exec_command("sudo python3 /home/pi/SDL_Starter.py")
                rprint(
                    "[green]Successfully enabled HIGH frequency logging (32 Hz)[/green]"
                )
            else:  # freq == "0"
                if not current_high_freq:
                    rprint("[yellow]Already running in LOW frequency mode[/yellow]")
                    return True
                rprint("[yellow]Stopping HIGH frequency logging...[/yellow]")
                ssh.exec_command("sudo python3 /home/pi/SDL_Stopper.py")
                rprint(
                    "[green]Successfully disabled HIGH frequency logging (returning to 1 Hz)[/green]"
                )

        except Exception as e:
            raise Exception(f"Failed to run frequency control script: {str(e)}")

    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")
        # If there's an error, try to close the SSH connection
        SSHClient.get_instance().close()
        return False

    return True
