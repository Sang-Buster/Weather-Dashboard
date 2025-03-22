#!/usr/bin/env python3
"""
UDP Receiver for Weather Logger Data

This script receives weather data sent via UDP from the Raspberry Pi weather logger.
Can be run standalone or as part of a Streamlit dashboard.
"""

import argparse
import json
import logging
import socket
import time
from datetime import datetime

import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(asctime)s] %(message)s",
    datefmt="%H:%M:%S",
)


class UDPReceiver:
    """Receives and processes weather data sent via UDP."""

    def __init__(self, bind_ip="0.0.0.0", bind_port=5555, save_to_file=False):
        """Initialize the UDP receiver."""
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.save_to_file = save_to_file
        self.socket = None
        self.log_file = None
        self.running = False

    def start(self):
        """Start the UDP receiver."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Enable broadcast if binding to all interfaces
        if self.bind_ip == "0.0.0.0":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            logging.info("UDP broadcast mode enabled")

        self.socket.bind((self.bind_ip, self.bind_port))
        logging.info(
            f"UDP receiver started, listening on {self.bind_ip}:{self.bind_port}"
        )

        # Open log file if saving to file
        if self.save_to_file:
            filename = f"weather_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.log_file = open(filename, "w")
            self.log_file.write(
                "timestamp,u_m_s,v_m_s,w_m_s,speed_2d,speed_3d,azimuth,elevation,pressure,temperature,humidity,sonic_temp,error\n"
            )
            logging.info(f"Logging data to {filename}")

        self.running = True

        try:
            self.receive_loop()
        except KeyboardInterrupt:
            logging.info("Receiver stopped by user")
        finally:
            self.stop()

    def stop(self):
        """Stop the UDP receiver."""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.log_file:
            self.log_file.close()
        logging.info("UDP receiver stopped")

    def receive_loop(self):
        """Main loop to receive and process UDP packets."""
        packet_count = 0
        last_log_time = time.time()
        last_packet_time = time.time()
        consecutive_missed = 0
        max_consecutive_missed = 10  # Threshold for warning

        while self.running:
            try:
                self.socket.settimeout(0.5)
                data, addr = self.socket.recvfrom(2048)
                packet_count += 1
                current_time = time.time()

                # Calculate time since last packet
                time_since_last = current_time - last_packet_time
                last_packet_time = current_time

                # Check for significant delays between packets
                if time_since_last > 2.0:  # More than 2 seconds between packets
                    consecutive_missed += 1
                    if consecutive_missed >= max_consecutive_missed:
                        logging.warning(
                            f"[INFO] No data received for {time_since_last:.2f}s"
                        )
                        consecutive_missed = 0
                else:
                    consecutive_missed = 0

                # Process received data
                self.process_data(data, addr)

                # Log stats every 10 seconds
                if current_time - last_log_time >= 10:
                    actual_rate = packet_count / (current_time - last_log_time)
                    logging.info(
                        f"[INFO] Current data rate: {actual_rate:.2f} Hz (received {packet_count} packets in last 10s)"
                    )
                    packet_count = 0
                    last_log_time = current_time

            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"Error receiving data: {e}")

    def process_data(self, data, addr):
        """Process received UDP data."""
        try:
            json_data = json.loads(data.decode("utf-8"))
            timestamp = json_data["timestamp"]

            # Format timestamp if needed
            try:
                if "T" in timestamp:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                logging.error(f"Error formatting timestamp: {e}")
                timestamp = "Invalid timestamp"

            # Format data as CSV
            csv_line = (
                f"{timestamp},"
                f"{json_data['u_m_s']},"
                f"{json_data['v_m_s']},"
                f"{json_data['w_m_s']},"
                f"{json_data['speed_2d']},"
                f"{json_data['speed_3d']},"
                f"{json_data['azimuth']},"
                f"{json_data['elevation']},"
                f"{json_data['pressure']},"
                f"{json_data['temperature']},"
                f"{json_data['humidity']},"
                f"{json_data['sonic_temp']},"
                f"{json_data['error']}"
            )

            print(csv_line)

            # Save to file if enabled
            if self.save_to_file and self.log_file:
                self.log_file.write(csv_line + "\n")
                self.log_file.flush()

        except json.JSONDecodeError:
            logging.warning(
                f"[INFO] Received invalid JSON data from {addr[0]}:{addr[1]}"
            )
        except Exception as e:
            logging.error(f"Error processing data: {e}")


def get_config():
    """Get configuration from either command line or environment variables."""
    # Try to get config from command line first
    parser = argparse.ArgumentParser(description="Receive weather data via UDP")
    parser.add_argument(
        "--ip", type=str, default="0.0.0.0", help="IP address to bind to"
    )
    parser.add_argument("--port", type=int, default=5555, help="UDP port to listen on")
    parser.add_argument(
        "--save", action="store_true", help="Save received data to CSV file"
    )
    args = parser.parse_args()

    # If running as standalone script, use command line args
    if __name__ == "__main__":
        return args.ip, args.port, args.save

    # If running as part of Streamlit app, try to use secrets
    try:
        secrets = st.secrets["udp_receiver"]
        return (
            secrets.get("bind_ip", "0.0.0.0"),
            secrets.get("bind_port", 5555),
            secrets.get("save_to_file", False),
        )
    except Exception as e:
        logging.warning(f"Could not load secrets, using defaults: {e}")
        return "0.0.0.0", 5555, False


def main():
    """Main entry point for the UDP receiver."""
    bind_ip, bind_port, save_to_file = get_config()

    # Create and start receiver
    receiver = UDPReceiver(bind_ip, bind_port, save_to_file)
    receiver.start()


if __name__ == "__main__":
    main()
