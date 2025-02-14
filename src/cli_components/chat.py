import atexit
import select
import socket
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import re

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
                result = s.connect_ex((st.secrets["ollama"]["host"], OLLAMA_PORT))
                return result == 0
        except socket.error:
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
            self.forward_socket.bind((st.secrets["ollama"]["host"], OLLAMA_PORT))
            self.forward_socket.listen(1)

            # Start forwarding in a separate thread
            def forward():
                try:
                    while True:
                        try:
                            client, addr = self.forward_socket.accept()
                            channel = self.transport.open_channel(
                                "direct-tcpip",
                                (st.secrets["ollama"]["host"], OLLAMA_PORT),
                                addr,
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
                    result = s.connect_ex((st.secrets["ollama"]["host"], OLLAMA_PORT))
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


def get_available_dates() -> List[str]:
    """Get list of available dates with weather data."""
    try:
        data_dir = Path(WEATHER_DATA_PATH)
        csv_files = list(data_dir.glob("*_weather_station_data.csv"))
        dates = [f.stem.split("_")[0:3] for f in csv_files]
        return ["_".join(date) for date in dates]
    except Exception as e:
        rprint(f"[red]Error getting available dates: {str(e)}[/red]")
        return []


def read_weather_data(date: str) -> Optional[Dict[str, Any]]:
    """Read weather data for a specific date and return statistics."""
    DEBUG = True

    def debug_print(message: str, color: str = "blue"):
        """Helper function for debug printing"""
        if DEBUG:
            rprint(f"[{color}]{message}[/{color}]")

    def safe_float(value):
        """Helper function to safely convert to float"""
        try:
            if pd.isna(value):
                return 0.0
            if hasattr(value, "iloc"):
                return float(value.iloc[0])
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    try:
        file_path = Path(WEATHER_DATA_PATH) / f"{date}_weather_station_data.csv"
        if not file_path.exists():
            if DEBUG:
                debug_print(f"File not found: {file_path}", "yellow")
            return None

        # Read the entire file first to get total records
        df = pd.read_csv(file_path)
        df["tNow"] = pd.to_datetime(df["tNow"])

        if DEBUG:
            debug_print(f"Processing {len(df)} records from {file_path}", "blue")

        # Ensure data is sorted by time
        df = df.sort_values("tNow")

        # Set the time index to start at midnight and end at 23:59:59
        start_time = df["tNow"].dt.normalize().iloc[0]  # Get start of day
        end_time = start_time + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        # Resample to hourly intervals (24 hours)
        df = df.set_index("tNow")
        df = df.loc[start_time:end_time]  # Trim to exact day

        agg_dict = {
            "Temp_C": ["mean", "min", "max"],
            "SonicTemp_C": ["mean", "min", "max"],
            "2dSpeed_m_s": ["mean", "min", "max"],
            "3DSpeed_m_s": ["mean", "min", "max"],
            "u_m_s": ["mean", "min", "max"],
            "v_m_s": ["mean", "min", "max"],
            "w_m_s": ["mean", "min", "max"],
            "Azimuth_deg": "mean",
            "Elev_deg": ["mean", "min", "max"],
            "Press_Pa": ["mean", "min", "max"],
            "Hum_RH": ["mean", "min", "max"],
        }

        # Resample with fixed 24-hour periods
        df_hourly = df.resample(rule="h", closed="left", label="left").agg(agg_dict)

        if DEBUG:
            debug_print(f"Original records: {len(df)}", "blue")
            debug_print(f"Resampled to {len(df_hourly)} hourly intervals", "blue")
            debug_print(f"Time range: {df.index.min()} to {df.index.max()}", "blue")

        # Create stats structure with only hourly data
        stats = {
            "date": date,
            "total_records": len(df),
            "hours_recorded": len(df_hourly),
            "data_columns": list(agg_dict.keys()),  # List available columns
            "sample_hour": {  # Show just one hour as example
                "hour": 0,
                "timestamp": df_hourly.index[0].strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": {
                    "mean": safe_float(df_hourly["Temp_C"]["mean"].iloc[0]),
                    "min": safe_float(df_hourly["Temp_C"]["min"].iloc[0]),
                    "max": safe_float(df_hourly["Temp_C"]["max"].iloc[0]),
                },
                "sonic_temperature": {
                    "mean": safe_float(df_hourly["SonicTemp_C"]["mean"].iloc[0]),
                    "min": safe_float(df_hourly["SonicTemp_C"]["min"].iloc[0]),
                    "max": safe_float(df_hourly["SonicTemp_C"]["max"].iloc[0]),
                },
                "wind": {
                    "speed_2d": {
                        "mean": safe_float(df_hourly["2dSpeed_m_s"]["mean"].iloc[0]),
                        "min": safe_float(df_hourly["2dSpeed_m_s"]["min"].iloc[0]),
                        "max": safe_float(df_hourly["2dSpeed_m_s"]["max"].iloc[0]),
                    },
                    "speed_3d": {
                        "mean": safe_float(df_hourly["3DSpeed_m_s"]["mean"].iloc[0]),
                        "min": safe_float(df_hourly["3DSpeed_m_s"]["min"].iloc[0]),
                        "max": safe_float(df_hourly["3DSpeed_m_s"]["max"].iloc[0]),
                    },
                    "components": {
                        "u": {"mean": safe_float(df_hourly["u_m_s"]["mean"].iloc[0])},
                        "v": {"mean": safe_float(df_hourly["v_m_s"]["mean"].iloc[0])},
                        "w": {"mean": safe_float(df_hourly["w_m_s"]["mean"].iloc[0])},
                    },
                    "direction": {
                        "azimuth": {
                            "mean": safe_float(df_hourly["Azimuth_deg"].iloc[0])
                        },
                        "elevation": {
                            "mean": safe_float(df_hourly["Elev_deg"]["mean"].iloc[0]),
                            "min": safe_float(df_hourly["Elev_deg"]["min"].iloc[0]),
                            "max": safe_float(df_hourly["Elev_deg"]["max"].iloc[0]),
                        },
                    },
                },
                "humidity": {
                    "mean": safe_float(df_hourly["Hum_RH"]["mean"].iloc[0]),
                    "min": safe_float(df_hourly["Hum_RH"]["min"].iloc[0]),
                    "max": safe_float(df_hourly["Hum_RH"]["max"].iloc[0]),
                },
                "pressure": {
                    "mean": safe_float(df_hourly["Press_Pa"]["mean"].iloc[0]),
                    "min": safe_float(df_hourly["Press_Pa"]["min"].iloc[0]),
                    "max": safe_float(df_hourly["Press_Pa"]["max"].iloc[0]),
                },
            },
        }

        if DEBUG:
            debug_print("Processed weather data:", "green")
            debug_print(json.dumps(stats, indent=2), "green")

        return stats

    except Exception as e:
        debug_print(f"Error reading weather data for {date}: {str(e)}", "red")
        return None


def get_mapped_dates(text: str) -> List[str]:
    """Map date references to actual available dates."""
    available_dates = get_available_dates()
    if not available_dates:
        return []

    # Convert available dates to datetime objects for comparison
    available_dates_dt = {
        datetime.strptime(date, "%Y_%m_%d"): date  # Remove timezone info
        for date in available_dates
    }

    # Get latest date
    latest_date = max(available_dates_dt.keys())

    text_lower = text.lower()

    # Time period mappings
    time_mappings = {
        "today": lambda: [latest_date.strftime("%Y_%m_%d")],
        "yesterday": lambda: [(latest_date - timedelta(days=1)).strftime("%Y_%m_%d")],
        "this week": lambda: [
            (latest_date - timedelta(days=i)).strftime("%Y_%m_%d")
            for i in range(7)
            if (latest_date - timedelta(days=i)).strftime("%Y_%m_%d") in available_dates
        ],
        "last week": lambda: [
            (latest_date - timedelta(days=i)).strftime("%Y_%m_%d")
            for i in range(7, 14)
            if (latest_date - timedelta(days=i)).strftime("%Y_%m_%d") in available_dates
        ],
        "this month": lambda: [
            d.strftime("%Y_%m_%d")
            for d in available_dates_dt.keys()
            if d.year == latest_date.year and d.month == latest_date.month
        ],
        "last month": lambda: [
            d.strftime("%Y_%m_%d")
            for d in available_dates_dt.keys()
            if (d.year == latest_date.year and d.month == latest_date.month - 1)
            or (
                latest_date.month == 1
                and d.year == latest_date.year - 1
                and d.month == 12
            )
        ],
    }

    # Check for time period references first
    for period, date_func in time_mappings.items():
        if period in text_lower:
            dates = date_func()
            if dates:  # Only return if we found valid dates
                return sorted(dates)

    # If no time periods found, check for YYYY_MM_DD format
    date_matches = re.findall(r"\d{4}[-_]\d{2}[-_]\d{2}", text)
    if date_matches:
        normalized_dates = [d.replace("-", "_") for d in date_matches]
        valid_dates = [d for d in normalized_dates if d in available_dates]
        if valid_dates:
            if len(valid_dates) >= 2:
                start = datetime.strptime(valid_dates[0], "%Y_%m_%d")
                end = datetime.strptime(valid_dates[-1], "%Y_%m_%d")
                # Generate all dates between start and end
                date_list = []
                current = start
                while current <= end:
                    date_str = current.strftime("%Y_%m_%d")
                    if date_str in available_dates:
                        date_list.append(date_str)
                    current += timedelta(days=1)
                return date_list
            return valid_dates

    return []


def parse_date_reference(text: str) -> List[str]:
    """Parse date references from text and return YYYY_MM_DD formatted dates."""
    mapped_dates = get_mapped_dates(text)
    if mapped_dates:
        return sorted(mapped_dates)
    return []


async def chat_with_llm(prompt: str, model: str = None) -> str:
    """Chat with Ollama LLM model with structured function calling."""
    DEBUG = True

    def debug_print(message: str, color: str = "blue"):
        """Helper function for debug printing"""
        if DEBUG:
            rprint(f"[{color}]{message}[/{color}]")

    try:
        ssh_forwarder.acquire()
        time.sleep(0.5)

        system_prompt = """You are Meteorix, a professional meteorologist bot created by Sang-Buster. 
You have access to weather station data through functions.

IMPORTANT: All dates must be in YYYY_MM_DD format with underscores (not hyphens).
For example: 2024_10_08 (correct) vs 2024-10-08 (incorrect)

Available weather metrics:
- Temperature (Temp_C, SonicTemp_C)
- Wind (2dSpeed_m_s, 3DSpeed_m_s, u_m_s, v_m_s, w_m_s)
- Wind Direction (Azimuth_deg: 0-360°, Elev_deg: -60° to +60°)
- Humidity (Hum_RH)
- Pressure (Press_Pa)

When analyzing weather data, please provide a detailed analysis including:
   - Temperature analysis (both regular and sonic, in °C and °F)
   - Wind analysis:
     * 2D and 3D wind speeds (in m/s and mph)
     * Wind components (u, v, w)
     * Wind direction (azimuth and elevation angles)
   - Humidity levels and their implications
   - Pressure readings and their meaning
   - Notable patterns or extreme values
   - General weather conditions summary

Remember to:
- Always use YYYY_MM_DD format with underscores
- Convert units appropriately (°C to °F, m/s to mph, Pa to hPa)
- Explain what the values mean for everyday activities
- Provide context about the weather conditions
- Always sign your analysis with "🌦️[Meteorix](https://github.com/Sang-Buster/weather-dashboard)🌦️ | Created by 😎[Sang-Buster](https://github.com/Sang-Buster)😎"
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        client = AsyncClient(host=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}")
        model = model or DEFAULT_MODEL

        response_text = ""
        data_context = ""

        try:
            # Step 1: Get the function call
            debug_print("Getting function call...", "yellow")
            response = await client.chat(model=model, messages=messages)

            if not response or not hasattr(response, "message"):
                debug_print("Error: Invalid response from Ollama", "red")
                return None

            initial_response = response.message.content
            if DEBUG:
                debug_print("Raw response:", "blue")
                debug_print(initial_response, "blue")

            # Try to extract dates from the prompt first
            dates = parse_date_reference(prompt)

            if dates:
                debug_print(f"Found dates in prompt: {dates}", "yellow")
                data_context = ""

                # Get data for each date
                available_dates = get_available_dates()
                for date in dates:
                    if date in available_dates:
                        data = read_weather_data(date)
                        if data:
                            data_context += f"\nData for {date}:\n"
                            data_context += json.dumps(data, indent=2)
                            data_context += "\n"
                            debug_print(f"Got data for date {date}")

                if data_context:
                    # Remove redundant debug prints
                    debug_print("Requesting analysis...", "yellow")

                    # Create analysis messages
                    analysis_messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                        {
                            "role": "user",
                            "content": f"""Here is the requested weather data:
{data_context}

Please provide a concise but insightful analysis of this weather data. Focus on:

1. Significant Weather Events and Anomalies:
   - Any unusual or extreme conditions
   - Notable weather transitions
   - Potentially hazardous conditions

2. Daily Weather Patterns:
   - Key temperature trends (°C and °F)
   - Important wind pattern changes
   - Significant humidity or pressure shifts

3. Practical Implications:
   - Impact on daily activities
   - Best and worst times for outdoor activities
   - Safety considerations if applicable

Keep the analysis natural and flowing, avoiding bullet-point lists of raw data. Focus on telling the weather "story" and highlight what's most important for people to know.

Remember to analyze the hourly changes since we have 24 data points per day, but only mention specific hours when they're significant.
Sign with "🌦️[Meteorix](https://github.com/Sang-Buster/weather-dashboard)🌦️ | Created by 😎[Sang-Buster](https://github.com/Sang-Buster)😎".""",
                        },
                    ]

                    # Get the analysis
                    debug_print("Getting analysis...", "yellow")
                    try:
                        analysis_response = await client.chat(
                            model=model, messages=analysis_messages
                        )

                        if analysis_response and hasattr(analysis_response, "message"):
                            response_text = analysis_response.message.content
                            if response_text and response_text.strip():
                                debug_print("Analysis complete", "green")
                                print("\n" + response_text + "\n")
                                return response_text
                    except Exception as e:
                        debug_print(f"Error during analysis: {str(e)}", "red")
                        return f"An error occurred during analysis: {str(e)}"
            else:
                # If no dates found, just return the initial response
                debug_print(
                    "No dates found in prompt, returning initial response", "yellow"
                )
                print("\n" + initial_response + "\n")
                return initial_response

            return "I apologize, but I couldn't find any weather data for the requested dates."

        except Exception as e:
            debug_print(f"Error during chat: {str(e)}", "red")
            return f"An error occurred: {str(e)}"

    except Exception as e:
        debug_print(f"Error connecting to Ollama: {str(e)}", "red")
        return None
    finally:
        ssh_forwarder.release()


def handle_chat_command(args):
    """Handle the chat command with arguments."""
    # Handle 'chat models' subcommand
    if args.action_or_prompt == "models":
        available_models = get_available_models()
        rprint("\n[bold]Available Models:[/bold]")
        for model in available_models:
            rprint(f"• {model}")
        rprint('\nUse with: meteorix chat --model <model_name> "your prompt"\n')
        return

    # Combine all prompt parts
    prompt = ""
    if isinstance(args.action_or_prompt, list):
        prompt = " ".join(args.action_or_prompt)
    elif args.action_or_prompt:
        prompt = args.action_or_prompt
    if hasattr(args, "remaining_prompt") and args.remaining_prompt:
        prompt += " " + " ".join(args.remaining_prompt)

    # Regular chat command handling
    if not prompt:
        rprint("[red]Error: Please provide a prompt for the chat.[/red]")
        rprint("[yellow]Usage examples:[/yellow]")
        rprint('  meteorix chat "How\'s the weather today?"')
        rprint('  meteorix chat "What was the weather like yesterday?"')
        rprint('  meteorix chat "Show me the weather for last week"')
        rprint("[yellow]To see available models: `meteorix chat models`[/yellow]")
        return

    # Return the chat coroutine
    return chat_with_llm(prompt, args.model)


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
