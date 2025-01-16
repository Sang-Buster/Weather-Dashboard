import paramiko
from rich import print as rprint
import socket
import streamlit as st
from pathlib import Path
from threading import Lock


class SSHClient:
    _instance = None
    _lock = Lock()
    _client = None
    _last_address = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        if SSHClient._instance:
            raise Exception("This class is a singleton. Use get_instance() instead.")
        SSHClient._instance = self

    def get_client(self, address):
        """Get or create SSH client with connection check"""
        try:
            # If client exists, check if it's still alive and connected to the right address
            if self._client and self._last_address == address:
                try:
                    rprint("[yellow]Checking existing connection...[/yellow]")
                    self._client.exec_command("echo 1", timeout=2)
                    rprint("[green]Reusing existing SSH connection[/green]")
                    return self._client
                except Exception:
                    # Connection is dead, close it
                    rprint(
                        "[yellow]Existing connection dead, creating new one...[/yellow]"
                    )
                    self._client.close()
                    self._client = None

            # Create new connection if needed
            if not self._client:
                rprint("[yellow]Creating new SSH connection...[/yellow]")
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=address,
                    username=st.secrets["weatherstation"]["user"],
                    password=st.secrets["weatherstation"]["password"],
                    timeout=5,
                )
                self._client = client
                self._last_address = address
                rprint("[green]Successfully connected to Pi![/green]")

            return self._client

        except Exception as e:
            if self._client:
                self._client.close()
                self._client = None
            raise Exception(f"SSH connection failed: {str(e)}")

    def close(self):
        """Close the SSH connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._last_address = None


def find_pi_address():
    """Try use direct IP connection to find the Raspberry Pi's address"""
    try:
        rprint("[yellow]Trying direct IP connection...[/yellow]")
        # Read IP from file instead of hardcoding
        ip_file = Path("/var/tmp/wx/last_ip.txt")
        if ip_file.exists():
            address = ip_file.read_text().strip()
        else:
            return None

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((address, 22))
        sock.close()

        if result == 0:
            rprint(f"[green]Successfully found Pi at {address} via direct IP[/green]")
            return address
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")
        return None

    return None


def get_pi_ip():
    """Get IP address information from the Raspberry Pi weather station"""
    try:
        # Find the Pi's current address
        pi_address = find_pi_address()
        if not pi_address:
            raise Exception("Could not locate the Raspberry Pi on the network")

        # Get SSH client instance
        ssh = SSHClient.get_instance().get_client(pi_address)

        # Run commands to get network info
        commands = [
            "hostname -I",  # Get all IP addresses
            "nmcli dev wifi",  # Get WiFi info using NetworkManager
            "ip -br addr",  # Get interface info (modern replacement for ifconfig)
            "ip route",  # Get routing info
        ]

        network_info = {}
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            network_info[cmd] = stdout.read().decode()
            error = stderr.read().decode()
            if error and "command not found" not in error:
                rprint(f"[yellow]Warning when running {cmd}: {error}[/yellow]")

        # Parse and display results
        rprint(f"\n[bold blue]{'='*60}[/bold blue]")
        rprint("[bold green]Raspberry Pi Network Status[/bold green]")
        rprint(f"[bold blue]{'='*60}[/bold blue]\n")

        # Show hostname resolution method
        rprint(f"[yellow]Current Address:[/yellow] {pi_address}")

        # Show IP addresses
        ips = network_info["hostname -I"].strip().split()
        if ips:
            rprint("\n[yellow]IP Addresses:[/yellow]")
            for ip in ips:
                rprint(f"  • {ip}")

        # Show WiFi network and signal strength
        wifi_info = network_info["nmcli dev wifi"].strip()
        if wifi_info:
            lines = wifi_info.split("\n")
            if len(lines) >= 2:  # Check if we have header and data
                for line in lines[1:]:  # Skip header line
                    if "*" in line:  # Current connection has asterisk
                        parts = line.split()
                        if len(parts) >= 8:
                            bssid = parts[1]
                            ssid = parts[2]
                            mode = parts[3]
                            chan = parts[4]
                            rate = parts[5] + " " + parts[6]  # Combine rate and unit
                            signal = parts[7]  # SIGNAL column
                            bars = parts[8]  # BARS column
                            security = parts[9] if len(parts) > 9 else "--"

                            rprint("\n[yellow]WiFi Network Details:[/yellow]")
                            rprint(f"  • SSID: {ssid}")
                            rprint(f"  • BSSID: {bssid}")
                            rprint(f"  • Mode: {mode}")
                            rprint(f"  • Channel: {chan}")
                            rprint(f"  • Rate: {rate}")

                            # Convert signal strength (0-100) to our format
                            try:
                                signal_percent = int(signal)
                                signal_dbm = int(
                                    (signal_percent / 2) - 100
                                )  # Rough conversion
                                our_bars = "▓" * (signal_percent // 20) + "░" * (
                                    5 - signal_percent // 20
                                )
                                rprint(
                                    f"  • Signal Strength: {our_bars} ({signal_dbm} dBm, {signal_percent}%)"
                                )
                                rprint(f"  • Network Bars: {bars}")
                            except ValueError:
                                rprint(f"  • Signal Strength: {signal}")
                                rprint(f"  • Network Bars: {bars}")

                            rprint(f"  • Security: {security}")
                            break

        # Parse ip addr for interface info
        rprint("\n[yellow]Network Interfaces:[/yellow]")
        for line in network_info["ip -br addr"].split("\n"):
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    interface = parts[0]
                    state = parts[1]
                    addresses = parts[2:]
                    rprint(f"  • {interface}: {state}")
                    for addr in addresses:
                        rprint(f"    ↳ {addr}")

        # Show routing information
        rprint("\n[yellow]Routing Information:[/yellow]")
        for line in network_info["ip route"].split("\n"):
            if line.strip():
                if "default via" in line:
                    gateway = line.split("via")[1].split()[0]
                    rprint(f"  • Default Gateway: {gateway}")

        rprint(f"\n[bold blue]{'='*60}[/bold blue]")
        return True

    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")
        # If there's an error, try to close the connection to allow for a fresh start next time
        SSHClient.get_instance().close()
        return False
