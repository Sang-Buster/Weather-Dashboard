import atexit
import select
import socket
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import paramiko
import streamlit as st
from ollama import AsyncClient, Client
from rich import print as rprint

from src import CSV_DIR

# Constants from secrets
OLLAMA_PORT = st.secrets["ollama"]["port"]
OLLAMA_HOST = st.secrets["ollama"]["host"]
SSH_JUMP_HOST = st.secrets["ollama"]["ssh_host"]
SSH_TARGET = st.secrets["ollama"]["ssh_target"]
DEFAULT_MODEL = st.secrets["ollama"]["model"]
WEATHER_DATA_PATH = CSV_DIR


class SSHPortForward:
    def __init__(self):
        self.transport = None
        self.jump_client = None
        self.target_client = None
        self.forward_socket = None
        self.forward_thread = None
        self._active_connections = 0  # Track number of active users
        self._lock = threading.Lock()  # Thread-safe counter
        self._connection_status = "closed"  # Track connection status
        self._last_used = None  # Track when connection was last used
        self._cleanup_task = None
        self._connection_timeout = 300  # Keep connection alive for 5 minutes

    def acquire(self):
        """Increment connection counter and start if needed"""
        with self._lock:
            current_time = time.time()
            self._last_used = current_time

            if self._connection_status == "closed":
                rprint("[yellow]Establishing SSH connection...[/yellow]")
                self.start()
                self._connection_status = "open"
                # Start cleanup task
                self._start_cleanup_task()
            else:
                rprint("[green]Reusing existing SSH connection[/green]")

            self._active_connections += 1

    def release(self):
        """Decrement connection counter"""
        with self._lock:
            self._active_connections = max(0, self._active_connections - 1)
            self._last_used = time.time()  # Update last used time

    def _start_cleanup_task(self):
        """Start the cleanup task in a separate thread"""
        if self._cleanup_task is None:
            self._cleanup_task = threading.Thread(target=self._cleanup_loop)
            self._cleanup_task.daemon = True
            self._cleanup_task.start()

    def _cleanup_loop(self):
        """Periodically check if connection should be closed"""
        while True:
            time.sleep(10)  # Check every 10 seconds
            with self._lock:
                if (
                    self._connection_status == "open"
                    and self._active_connections == 0
                    and self._last_used is not None
                    and time.time() - self._last_used > self._connection_timeout
                ):
                    rprint("[yellow]Closing inactive SSH connection[/yellow]")
                    self.stop()
                    self._connection_status = "closed"
                    self._cleanup_task = None
                    break

    def is_port_in_use(self):
        """Check if the port is already in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Set a short timeout
                s.settimeout(1)
                result = s.connect_ex(("127.0.0.1", OLLAMA_PORT))
                return result == 0
        except socket.error:
            return False

    def is_connection_active(self):
        """Check if the SSH connection is still active"""
        if self.transport and self.transport.is_active():
            try:
                # Try to use the connection
                self.transport.send_ignore()
                return True
            except Exception:
                return False
        return False

    def start(self):
        """Start SSH port forwarding with jump host"""
        try:
            # Always stop existing connections first
            self.stop()

            # Wait for port to be available
            retries = 5
            while self.is_port_in_use() and retries > 0:
                rprint(
                    f"[yellow]Waiting for port {OLLAMA_PORT} to be available... ({retries} retries left)[/yellow]"
                )
                time.sleep(1)
                retries -= 1

            if self.is_port_in_use():
                raise Exception(f"Port {OLLAMA_PORT} is still in use after waiting")

            # Create jump host connection
            self.jump_client = paramiko.SSHClient()
            self.jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            rprint("[yellow]Connecting to jump host...[/yellow]")
            # Connect to jump host
            jump_username = SSH_JUMP_HOST.split("@")[0]
            jump_hostname = SSH_JUMP_HOST.split("@")[1]
            self.jump_client.connect(
                jump_hostname,
                username=jump_username,
                password=st.secrets["ollama"]["ssh_password"],
            )

            rprint("[yellow]Connected to jump host, establishing tunnel...[/yellow]")
            # Create channel through jump host
            jump_transport = self.jump_client.get_transport()

            # Connect to target through jump host
            target_username = SSH_TARGET.split("@")[0]
            target_hostname = SSH_TARGET.split("@")[1]
            target_addr = (target_hostname, 22)
            jump_addr = ("localhost", 0)  # Use dynamic local port

            channel = jump_transport.open_channel(
                "direct-tcpip", target_addr, jump_addr
            )

            # Create target host connection
            self.target_client = paramiko.SSHClient()
            self.target_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to target through the channel
            self.target_client.connect(
                target_hostname,
                username=target_username,
                password=st.secrets["ollama"]["ssh_password"],
                sock=channel,
            )

            # Set up port forwarding
            self.transport = self.target_client.get_transport()

            # Create local forwarding socket
            self.forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.forward_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.forward_socket.bind(("127.0.0.1", OLLAMA_PORT))
            self.forward_socket.listen(1)

            # Start forwarding in a separate thread
            def forward():
                try:
                    while True:
                        try:
                            client, addr = self.forward_socket.accept()
                            channel = self.transport.open_channel(
                                "direct-tcpip", ("127.0.0.1", OLLAMA_PORT), addr
                            )
                            if channel is None:
                                client.close()
                                continue

                            thr = threading.Thread(
                                target=self.handler, args=(client, channel)
                            )
                            thr.daemon = True
                            thr.start()
                        except Exception as e:
                            if self.transport is None:
                                break
                            rprint(f"[yellow]Forward error: {str(e)}[/yellow]")
                except Exception:
                    pass
                finally:
                    if self.forward_socket:
                        try:
                            self.forward_socket.close()
                        except socket.error:
                            pass

            self.forward_thread = threading.Thread(target=forward)
            self.forward_thread.daemon = True
            self.forward_thread.start()

            time.sleep(2)  # Give more time for the connection to establish

            # Verify the connection
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    result = s.connect_ex(("127.0.0.1", OLLAMA_PORT))
                    if result == 0:
                        rprint("[green]Port forwarding verified and working[/green]")
                    else:
                        raise Exception("Port forwarding verification failed")
            except Exception as e:
                raise Exception(f"Port forwarding verification failed: {str(e)}")

        except Exception as e:
            rprint(f"[red]Failed to establish SSH port forwarding: {str(e)}[/red]")
            self.stop()
            raise

    def handler(self, client, channel):
        """Handle forwarded connection"""
        try:
            while True:
                r, w, x = select.select([client, channel], [], [])
                if client in r:
                    data = client.recv(1024)
                    if len(data) == 0:
                        break
                    channel.send(data)
                if channel in r:
                    data = channel.recv(1024)
                    if len(data) == 0:
                        break
                    client.send(data)
        except (socket.error, paramiko.SSHException):
            pass
        finally:
            channel.close()
            client.close()

    def stop(self):
        """Stop SSH port forwarding and clean up connections"""
        # Stop the forwarding thread first
        if self.forward_socket:
            try:
                self.forward_socket.close()
            except socket.error:
                pass
            self.forward_socket = None

        if self.forward_thread:
            try:
                self.forward_thread.join(timeout=1)
            except threading.ThreadError:
                pass
            self.forward_thread = None

        if self.transport:
            try:
                self.transport.close()
            except paramiko.SSHException:
                pass
            self.transport = None

        if self.target_client:
            try:
                self.target_client.close()
            except paramiko.SSHException:
                pass
            self.target_client = None

        if self.jump_client:
            try:
                self.jump_client.close()
            except paramiko.SSHException:
                pass
            self.jump_client = None
        self._last_used = None
        if self._cleanup_task:
            self._cleanup_task = None


# Global SSH forwarder
ssh_forwarder = SSHPortForward()


def cleanup():
    """Cleanup function to stop SSH forwarding on exit"""
    ssh_forwarder.stop()


# Register cleanup function
atexit.register(cleanup)


def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit"""
    return (celsius * 9 / 5) + 32


def mps_to_mph(mps):
    """Convert meters per second to miles per hour"""
    return mps * 2.237


def categorize_wind_direction(degrees):
    """Convert azimuth degrees to cardinal directions."""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((degrees + 22.5) % 360 // 45)
    return directions[idx]


def get_dominant_wind_direction(directions):
    """Get the most common wind direction from a list."""
    from collections import Counter

    if not directions:
        return "N/A"
    return Counter(directions).most_common(1)[0][0]


def get_latest_reading(csv_path):
    """Get the most recent weather reading from a CSV file."""
    try:
        # Read only the last few rows for efficiency
        df = pd.read_csv(csv_path, nrows=10)
        if not df.empty:
            latest = df.iloc[-1]
            return {
                "timestamp": latest.get("tNow", "N/A"),
                "temp_c": latest.get("Temp_C", 0),
                "pressure": latest.get("Press_Pa", 0),
                "humidity": latest.get("Hum_RH", 0),
                "wind_speed": latest.get("3DSpeed_m_s", 0)
                if "3DSpeed_m_s" in df.columns
                else 0,
                "wind_dir": categorize_wind_direction(latest["Azimuth_deg"])
                if "Azimuth_deg" in df.columns
                else "N/A",
            }
    except Exception as e:
        rprint(f"[yellow]Warning: Could not read latest data: {str(e)}[/yellow]")
    return None


def get_recent_weather_data(days=7, start_date=None, end_date=None):
    """Get weather data for analysis."""
    try:
        data_dir = Path(WEATHER_DATA_PATH)

        # Get latest reading first
        current_date = datetime.now()
        today_str = current_date.strftime("%Y_%m_%d")
        today_file = data_dir / f"{today_str}_weather_station_data.csv"
        latest_reading = get_latest_reading(today_file) if today_file.exists() else None

        # If specific dates are provided, use those
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y_%m_%d")
                end = datetime.strptime(end_date, "%Y_%m_%d")
            except ValueError:
                return "Error: Dates must be in YYYY_MM_DD format"
        else:
            # Otherwise use last N days
            end = current_date
            start = end - timedelta(days=days)

        # Get list of CSV files
        all_data = []
        current = start
        while current <= end:
            date_str = current.strftime("%Y_%m_%d")
            csv_path = data_dir / f"{date_str}_weather_station_data.csv"

            if csv_path.exists():
                try:
                    df = pd.read_csv(csv_path)

                    # Parse timestamps with microseconds
                    df["datetime"] = pd.to_datetime(df["tNow"], format="mixed")
                    df["hour"] = df["datetime"].dt.hour
                    df["minute"] = df["datetime"].dt.minute
                    df["interval"] = df["hour"] * 2 + (df["minute"] // 30)

                    # Get stats for each 30-minute interval
                    interval_stats = []
                    for interval in range(48):  # 48 30-minute intervals in a day
                        interval_data = df[df["interval"] == interval]
                        if not interval_data.empty:
                            hour = interval // 2
                            minute = (interval % 2) * 30
                            stats = {
                                "time": f"{hour:02d}:{minute:02d}",
                                "avg_temp_c": interval_data["Temp_C"].mean(),
                                "min_temp_c": interval_data["Temp_C"].min(),
                                "max_temp_c": interval_data["Temp_C"].max(),
                                "avg_humidity": interval_data["Hum_RH"].mean(),
                                "avg_pressure": interval_data["Press_Pa"].mean(),
                                "avg_wind_speed": interval_data["3DSpeed_m_s"].mean()
                                if "3DSpeed_m_s" in df.columns
                                else 0,
                                "records": len(interval_data),
                            }
                            interval_stats.append(stats)

                    # Calculate wind directions if column exists
                    dominant_direction = "N/A"
                    if "Azimuth_deg" in df.columns:
                        wind_directions = [
                            categorize_wind_direction(deg) for deg in df["Azimuth_deg"]
                        ]
                        dominant_direction = get_dominant_wind_direction(
                            wind_directions
                        )

                    # Daily statistics
                    stats = {
                        "date": date_str,
                        "intervals": interval_stats,
                        "avg_temp_c": df["Temp_C"].mean(),
                        "max_temp_c": df["Temp_C"].max(),
                        "min_temp_c": df["Temp_C"].min(),
                        "avg_pressure": df["Press_Pa"].mean(),
                        "avg_humidity": df["Hum_RH"].mean(),
                        "avg_wind_speed": df["3DSpeed_m_s"].mean()
                        if "3DSpeed_m_s" in df.columns
                        else 0,
                        "max_wind_speed": df["3DSpeed_m_s"].max()
                        if "3DSpeed_m_s" in df.columns
                        else 0,
                        "dominant_wind_dir": dominant_direction,
                        "records": len(df),
                        "latest_reading": df.iloc[-1] if not df.empty else None,
                    }
                    all_data.append(stats)

                except Exception as e:
                    rprint(
                        f"[yellow]Warning: Error reading {csv_path}: {str(e)}[/yellow]"
                    )
            else:
                rprint(f"[yellow]Warning: No data file found for {date_str}[/yellow]")

            current += timedelta(days=1)

        if not all_data and not latest_reading:
            return "No weather data available for the specified date range."

        # Format the data summary
        summary = ""

        # Add latest reading if available
        if latest_reading:
            temp_f = celsius_to_fahrenheit(latest_reading["temp_c"])
            wind_mph = mps_to_mph(latest_reading["wind_speed"])
            summary += f"Latest Reading ({latest_reading['timestamp']}):\n"
            summary += (
                f"• Temperature: {temp_f:.1f}°F ({latest_reading['temp_c']:.1f}°C)\n"
            )
            summary += f"• Humidity: {latest_reading['humidity']:.1f}%\n"
            summary += f"• Pressure: {latest_reading['pressure']:.1f} Pa\n"
            if latest_reading["wind_speed"] > 0:
                summary += f"• Wind: {wind_mph:.1f} mph ({latest_reading['wind_speed']:.1f} m/s) from {latest_reading['wind_dir']}\n"
            summary += "\n"

        # Add historical data
        if all_data:
            date_range = f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
            summary += f"Historical Data ({date_range}):\n\n"

            for day in all_data:
                summary += f"Date: {day['date']} ({day['records']} measurements)\n"

                # Add daily summary
                avg_f = celsius_to_fahrenheit(day["avg_temp_c"])
                min_f = celsius_to_fahrenheit(day["min_temp_c"])
                max_f = celsius_to_fahrenheit(day["max_temp_c"])

                summary += "Daily Summary:\n"
                summary += f"• Temperature: {avg_f:.1f}°F ({day['avg_temp_c']:.1f}°C)\n"
                summary += f"  - High: {max_f:.1f}°F ({day['max_temp_c']:.1f}°C)\n"
                summary += f"  - Low: {min_f:.1f}°F ({day['min_temp_c']:.1f}°C)\n"
                summary += f"• Pressure: {day['avg_pressure']:.1f} Pa\n"
                summary += f"• Humidity: {day['avg_humidity']:.1f}%\n"

                # Add 30-minute interval data (limited to prevent token overflow)
                if day["intervals"]:
                    summary += "\n30-Minute Intervals:\n"
                    for interval in day["intervals"][:12]:  # Show first 6 hours
                        temp_f = celsius_to_fahrenheit(interval["avg_temp_c"])
                        summary += f"• {interval['time']}: {temp_f:.1f}°F ({interval['avg_temp_c']:.1f}°C), "
                        summary += f"Humidity: {interval['avg_humidity']:.1f}%, "
                        summary += f"Pressure: {interval['avg_pressure']:.1f} Pa\n"
                    if len(day["intervals"]) > 12:
                        summary += "  ... (remaining intervals omitted)\n"

                summary += "\n"

        return summary

    except Exception as e:
        return f"Error reading weather data: {str(e)}"


def check_ollama_connection(retries=3, delay=1):
    """Check if we can connect to Ollama"""
    for i in range(retries):
        try:
            client = Client(host=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}")
            client.list()
            return True
        except Exception:
            if i < retries - 1:
                time.sleep(delay)
    return False


def get_available_models() -> list[str]:
    """Get list of available Ollama models."""
    try:
        # Acquire connection
        ssh_forwarder.acquire()

        # Wait longer for connection to be ready
        time.sleep(2)  # Add extra delay before checking connection

        if not check_ollama_connection(retries=5, delay=2):
            raise Exception("Could not connect to Ollama after port forwarding")

        # Initialize Ollama client
        client = Client(host=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}")

        # Get list of models
        response = client.list()

        # Extract model names from ListResponse
        if hasattr(response, "models"):
            models = [model.model for model in response.models]
        elif isinstance(response, dict) and "models" in response:
            models = [model["name"] for model in response["models"]]
        elif isinstance(response, list):
            models = [
                model["name"] if isinstance(model, dict) else model.model
                for model in response
            ]
        else:
            rprint(
                f"[yellow]Unexpected response format from Ollama: {type(response)}[/yellow]"
            )
            models = [DEFAULT_MODEL]

        if not models:
            models = [DEFAULT_MODEL]

        models.sort()
        return models

    except Exception as e:
        rprint(f"[red]Error getting model list: {str(e)}[/red]")
        return [DEFAULT_MODEL]
    finally:
        # Release connection
        ssh_forwarder.release()


async def chat_with_llm(prompt: str, model: str = None) -> str:
    """Chat with Ollama LLM model."""
    try:
        # Acquire connection
        ssh_forwarder.acquire()

        # Reduced wait time since connection should be ready
        time.sleep(0.5)  # Reduced from 2 seconds

        # Get weather data context
        weather_context = get_recent_weather_data()

        enhanced_prompt = f"""You are a professional meteorologist analyzing weather station data. Here is the weather data:

{weather_context}

Please provide a comprehensive meteorological analysis, paying special attention to unusual patterns and weather events:

1. Detailed Temperature Analysis:
   • Hour-by-hour temperature progression
   • Unusual temperature changes or anomalies
   • Rapid temperature shifts and their implications
   • Temperature inversions or unusual patterns
   • Comparison with expected patterns

2. Advanced Humidity & Pressure Analysis:
   • Significant pressure changes indicating weather systems
   • Unusual humidity patterns or sudden changes
   • Combinations indicating:
     - Storm development (rapid pressure drops + wind shifts)
     - Frontal passages (temperature + pressure changes)
     - Precipitation events (humidity + pressure patterns)
     - Severe weather potential (unstable conditions)

3. Wind Pattern Analysis:
   • Sudden wind direction shifts
   • Unusual gusting patterns
   • Wind speed variations indicating:
     - Storm approach
     - Front passage
     - Local weather effects
   • Correlation with pressure/temperature changes

4. Weather Event Identification:
   • Look for signatures of:
     - Thunderstorms (rapid pressure drops, wind shifts, temperature drops)
     - Cold/warm fronts (gradual pressure/temperature changes)
     - Microbursts (sudden wind direction changes, temperature drops)
     - Sea breezes (diurnal wind shifts)
     - Local terrain effects

5. Stability Analysis:
   • Indicators of atmospheric instability
   • Potential for severe weather development
   • Air mass characteristics and changes
   • Vertical temperature structure implications

6. Unusual Pattern Detection:
   • Identify any abnormal combinations of:
     - Temperature + humidity + pressure
     - Wind speed + direction + pressure
     - Rapid changes in multiple parameters
   • Compare with typical weather patterns
   • Explain potential causes and implications

7. Impact Assessment:
   • Practical implications of unusual patterns
   • Potential hazards or concerns
   • Expected duration of unusual conditions
   • Recommendations based on conditions

Please analyze with:
- Clear identification of unusual patterns
- Explanation of why patterns are significant
- Potential causes of unusual conditions
- Implications for local weather
- Safety considerations if applicable
- Both metric and imperial measurements
- Specific timestamps for significant changes

Based on this framework, please analyze:

{prompt}"""

        messages = [
            {
                "role": "system",
                "content": """You are MeteorologistGPT, a professional meteorologist created by Sang-Buster. You are:
- A weather expert who identifies and explains unusual patterns
- Trained in meteorological principles and data interpretation
- Skilled at recognizing weather event signatures
- Clear in explaining pattern significance and implications
- Precise in describing cause-and-effect relationships
- Proactive in highlighting potential weather hazards
- Fluent in meteorological terminology
- Practical in explaining weather implications
- Exact with timestamps and measurements
- Comfortable using both metric and imperial units

Always sign your analysis with:
"~ MeteorologistGPT, created by Sang-Buster"

Remember to maintain a professional yet approachable tone while providing comprehensive weather analysis.""",
            },
            {"role": "user", "content": enhanced_prompt},
        ]

        # Initialize Ollama client
        client = AsyncClient(host=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}")

        # Use model from secrets if none provided
        model = model or DEFAULT_MODEL

        # Generate response with streaming
        response_text = ""
        async for part in await client.chat(
            model=model, messages=messages, stream=True
        ):
            chunk = part["message"]["content"]
            print(chunk, end="", flush=True)
            response_text += chunk

        print()  # New line after response
        return response_text

    except Exception as e:
        rprint(f"[red]Error connecting to Ollama: {str(e)}[/red]")
        rprint(
            "[yellow]Make sure Ollama is running and the model is installed.[/yellow]"
        )
        rprint(
            f"[yellow]You can install the model with: 'ollama pull {model}'[/yellow]"
        )
        return None
    finally:
        # Release connection
        ssh_forwarder.release()


def handle_chat_command(args):
    """Handle the chat command with arguments."""

    # Handle 'chat models' subcommand
    if args.action_or_prompt == "models":
        # Get and display available models
        available_models = get_available_models()
        rprint("\n[bold]Available Models:[/bold]")
        for model in available_models:
            rprint(f"• {model}")
        rprint('\nUse with: meteorix chat --model <model_name> "your prompt"\n')
        return

    # Parse date range if provided
    start_date = None
    end_date = None
    prompt = ""

    # Combine all prompt parts
    if isinstance(args.action_or_prompt, list):
        prompt = " ".join(args.action_or_prompt)
    elif args.action_or_prompt:
        prompt = args.action_or_prompt
    if hasattr(args, "remaining_prompt") and args.remaining_prompt:
        prompt += " " + " ".join(args.remaining_prompt)

    # Look for date range in prompt
    if prompt:
        import re

        # Support multiple date range formats
        date_patterns = [
            r"from (\d{4}_\d{2}_\d{2}) to (\d{4}_\d{2}_\d{2})",  # from YYYY_MM_DD to YYYY_MM_DD
            r"between (\d{4}_\d{2}_\d{2}) and (\d{4}_\d{2}_\d{2})",  # between YYYY_MM_DD and YYYY_MM_DD
            r"(\d{4}_\d{2}_\d{2}) to (\d{4}_\d{2}_\d{2})",  # YYYY_MM_DD to YYYY_MM_DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, prompt)
            if match:
                start_date = match.group(1)
                end_date = match.group(2)
                # Remove the date range from the prompt
                prompt = re.sub(pattern, "", prompt).strip()
                break

    # Regular chat command handling
    if not prompt:
        rprint("[red]Error: Please provide a prompt for the chat.[/red]")
        rprint("[yellow]Usage examples:[/yellow]")
        rprint('  meteorix chat "How\'s the weather today?"')
        rprint('  meteorix chat "Analyze weather from 2024_10_08 to 2024_10_10"')
        rprint('  meteorix chat "Show data between 2024_10_08 and 2024_10_10"')
        rprint("[yellow]To see available models: `meteorix chat models`[/yellow]")
        return

    # Get weather data with optional date range
    weather_context = get_recent_weather_data(
        days=7,  # Default to last 7 days if no date range specified
        start_date=start_date,
        end_date=end_date,
    )

    # Create enhanced prompt with clearer instructions
    enhanced_prompt = f"""You are a weather station assistant. Here is the weather data:

{weather_context}

Note: This data represents all available measurements for the requested period. If data is missing or from a different time period, please inform the user.

Based on this data, please answer the following question:

{prompt}"""

    # Instead of asyncio.run(), return the coroutine
    return chat_with_llm(enhanced_prompt, args.model)


async def run_cli_command(ctx, args):
    """Run CLI command in async context."""
    try:
        # Get response from LLM
        response = await chat_with_llm(args[1], args.get("model"))
        if response:
            # Split long messages if needed
            MAX_LENGTH = 2000
            messages = [
                response[i : i + MAX_LENGTH]
                for i in range(0, len(response), MAX_LENGTH)
            ]
            for message in messages:
                await ctx.send(message)
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")
