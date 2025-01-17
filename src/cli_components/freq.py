from rich import print as rprint
from .ifconfig import SSHClient, find_pi_address


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

        # If no frequency specified, check current status
        if freq is None:
            # Check if the Weather Station logger is running using multiple methods
            # First check screen session
            stdin, stdout, stderr = ssh.exec_command("sudo screen -ls | grep logger")
            screen_output = stdout.read().decode().strip()

            if not screen_output:
                rprint("[yellow]Weather Station logger is not running[/yellow]")
                return

            # Check for active high frequency files
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

            # Check the actual frequency by looking at timestamps in real-time
            stdin, stdout, stderr = ssh.exec_command(
                f"tail -n 1 -f {latest_file} | head -n 2"
            )

            # Read two consecutive lines
            timestamps = []
            for _ in range(2):
                line = stdout.readline()
                if not line:
                    break
                timestamp_str = line.strip().split(",")[0]
                try:
                    stdin2, stdout2, stderr2 = ssh.exec_command(
                        f"date -d '{timestamp_str}' +%s.%N"
                    )
                    timestamp = float(stdout2.read().decode().strip())
                    timestamps.append(timestamp)
                except (ValueError, IndexError):
                    break

            # Calculate time difference and determine frequency
            if len(timestamps) == 2:
                time_diff = timestamps[1] - timestamps[0]
                is_high_freq = time_diff < 0.1
            else:
                is_high_freq = False

            # Display current status
            if current_time - file_time < 5 and is_high_freq:
                rprint(
                    "[green]Currently running in HIGH frequency mode (32 Hz)[/green]"
                )
                rprint(
                    f"[yellow]High frequency data being logged to: {latest_file}[/yellow]"
                )
            else:
                rprint("[green]Currently running in LOW frequency mode (1 Hz)[/green]")
                rprint(f"[yellow]Data being logged to: {latest_file}[/yellow]")
            return

        # Validate frequency input
        if freq not in ["0", "1"]:
            raise ValueError("Frequency must be '1' (32Hz) or '0' (1Hz)")

        try:
            # Run the appropriate script with sudo
            if freq == "1":
                rprint("[yellow]Starting HIGH frequency logging...[/yellow]")
                ssh.exec_command("sudo python3 /home/pi/SDL_Starter.py")
                rprint(
                    "[green]Successfully enabled HIGH frequency logging (32 Hz)[/green]"
                )
            else:
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
