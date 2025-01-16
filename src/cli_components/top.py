from rich import print as rprint
from .ifconfig import SSHClient, find_pi_address


def get_system_stats():
    """Get system statistics from Raspberry Pi"""
    try:
        # Find the Pi's current address
        pi_address = find_pi_address()
        if not pi_address:
            raise Exception("Could not locate the Raspberry Pi on the network")

        # Get SSH client instance
        ssh = SSHClient.get_instance().get_client(pi_address)

        # Commands to get various system metrics
        commands = {
            "loadavg": "cat /proc/loadavg",  # Load averages
            "memory": "free -h",  # Memory usage
            "cpu_temp": "vcgencmd measure_temp",  # CPU temperature
            "cpu_usage": "top -bn1 | grep '%Cpu'",  # CPU usage
            "disk": "df -h /",  # Disk usage for root partition
            "uptime": "uptime -p",  # System uptime
            "processes": "ps aux --sort=-%cpu | grep -v 'ps aux' | head -6",  # Top 5 CPU-consuming processes, excluding ps command
        }

        # Collect system information
        system_info = {}
        for key, cmd in commands.items():
            stdin, stdout, stderr = ssh.exec_command(cmd)
            system_info[key] = stdout.read().decode().strip()
            error = stderr.read().decode()
            if error and "command not found" not in error:
                rprint(f"[yellow]Warning when running {cmd}: {error}[/yellow]")

        # Parse and display results
        rprint(f"\n[bold blue]{'='*60}[/bold blue]")
        rprint("[bold green]Raspberry Pi System Status[/bold green]")
        rprint(f"[bold blue]{'='*60}[/bold blue]\n")

        # System Uptime
        rprint("[yellow]System Uptime:[/yellow]")
        rprint(f"  • {system_info['uptime']}\n")

        # Load Average
        load_1, load_5, load_15, *_ = system_info["loadavg"].split()
        rprint("[yellow]Load Average:[/yellow]")
        rprint(f"  • 1 min: {load_1}")
        rprint(f"  • 5 min: {load_5}")
        rprint(f"  • 15 min: {load_15}\n")

        # CPU Usage and Temperature
        rprint("[yellow]CPU Status:[/yellow]")
        cpu_usage = system_info["cpu_usage"].replace("  ", " ").split(",")
        user_cpu = cpu_usage[0].split()[1]
        system_cpu = cpu_usage[2].split()[0]
        idle_cpu = cpu_usage[3].split()[0]
        rprint(f"  • User: {user_cpu}%")
        rprint(f"  • System: {system_cpu}%")
        rprint(f"  • Idle: {idle_cpu}%")

        # Temperature
        temp = system_info["cpu_temp"].replace("temp=", "").replace("'C", "°C")
        rprint(f"  • Temperature: {temp}\n")

        # Memory Usage
        rprint("[yellow]Memory Usage:[/yellow]")
        memory_lines = system_info["memory"].split("\n")
        for line in memory_lines:
            if line.startswith("Mem:"):
                total, used, free, shared, buff_cache, available = line.split()[1:]
                rprint(f"  • Total: {total}")
                rprint(f"  • Used: {used}")
                rprint(f"  • Free: {free}")
                rprint(f"  • Buff/Cache: {buff_cache}")
                rprint(f"  • Available: {available}\n")

        # Disk Usage
        rprint("[yellow]Disk Usage:[/yellow]")
        disk_lines = system_info["disk"].split("\n")
        for line in disk_lines[1:]:  # Skip header
            fs, size, used, avail, use_percent, mount = line.split()
            rprint(f"  • Size: {size}")
            rprint(f"  • Used: {used} ({use_percent})")
            rprint(f"  • Available: {avail}\n")

        # Top Processes
        rprint("[yellow]Top Processes (CPU):[/yellow]")
        process_lines = system_info["processes"].split("\n")
        for line in process_lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 11:
                user = parts[0]
                pid = parts[1]
                cpu = parts[2]
                mem = parts[3]
                command = " ".join(parts[10:])
                rprint(
                    f"  • {user:<8} PID: {pid:<6} {command[:30]:<30} CPU: {cpu:>5}% MEM: {mem:>5}%"
                )

        rprint(f"\n[bold blue]{'='*60}[/bold blue]")
        return True

    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")
        # If there's an error, try to close the connection to allow for a fresh start next time
        SSHClient.get_instance().close()
        return False
