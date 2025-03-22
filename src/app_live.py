import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from collections import deque
from web_components_live.udp_receiver import UDPReceiver
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

# Set page config with dark theme
st.set_page_config(
    page_title="Live Weather Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None,
)

# Apply dark theme CSS
st.markdown(
    """
<style>
    .stApp {
        background-color: #0e1117;
        color: white;
    }
    .css-1544g2n {
        padding-top: 4rem;
    }
    .stMetric {
        background-color: #1e2129;
        padding: 10px;
        border-radius: 5px;
    }
    /* Add scrollable container */
    .main-content {
        max-height: 100vh;
        overflow-y: auto;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "data_buffer" not in st.session_state:
    st.session_state.data_buffer = {
        "timestamp": deque(maxlen=100),
        "wind_speed_2d": deque(maxlen=100),
        "wind_speed_3d": deque(maxlen=100),
        "azimuth": deque(maxlen=100),
        "elevation": deque(maxlen=100),
        "pressure": deque(maxlen=100),
        "temperature": deque(maxlen=100),
        "humidity": deque(maxlen=100),
        "sonic_temp": deque(maxlen=100),
    }

if "receiver" not in st.session_state:
    st.session_state.receiver = None

# Add pause control to session state
if "paused" not in st.session_state:
    st.session_state.paused = False

# Add update interval to session state (1 Hz by default)
if "update_interval" not in st.session_state:
    st.session_state.update_interval = 1.0

# Initialize plot containers
if "plot_containers" not in st.session_state:
    st.session_state.plot_containers = {
        "wind_rose": None,
        "temperature": None,
        "pressure": None,
        "metric_wind_speed": None,
        "metric_wind_direction": None,
        "metric_temperature": None,
        "metric_pressure": None,
        "metric_humidity": None,
    }


def process_data_for_dashboard(csv_line):
    """Process a CSV line and update the data buffers."""
    try:
        # Parse CSV line
        parts = csv_line.split(",")
        timestamp = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")

        # Update data buffers
        st.session_state.data_buffer["timestamp"].append(timestamp)
        st.session_state.data_buffer["wind_speed_2d"].append(float(parts[4]))
        st.session_state.data_buffer["wind_speed_3d"].append(float(parts[5]))
        st.session_state.data_buffer["azimuth"].append(float(parts[6]))
        st.session_state.data_buffer["elevation"].append(float(parts[7]))
        st.session_state.data_buffer["pressure"].append(float(parts[8]))
        st.session_state.data_buffer["temperature"].append(float(parts[9]))
        st.session_state.data_buffer["humidity"].append(float(parts[10]))
        st.session_state.data_buffer["sonic_temp"].append(float(parts[11]))
    except Exception as e:
        # Don't use st.error in this thread
        print(f"Error processing data: {e}")


class DashboardUDPReceiver(UDPReceiver):
    def process_data(self, data, addr):
        """Override process_data to update dashboard data."""
        try:
            json_data = self._parse_json_data(data)
            csv_line = self._format_csv_line(json_data)
            process_data_for_dashboard(csv_line)
        except Exception as e:
            # Don't use st.error in this thread
            print(f"Error in UDP receiver: {e}")

    def _parse_json_data(self, data):
        """Parse the JSON data from UDP packet."""
        import json

        return json.loads(data.decode("utf-8"))

    def _format_csv_line(self, json_data):
        """Format JSON data as CSV line."""
        timestamp = json_data["timestamp"]

        # Format timestamp if needed
        try:
            if "T" in timestamp:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
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

        return csv_line


def create_wind_rose():
    """Create a wind rose plot using the latest data."""
    if len(st.session_state.data_buffer["azimuth"]) == 0:
        return None

    # Create wind rose using plotly
    angles = list(st.session_state.data_buffer["azimuth"])
    speeds = list(st.session_state.data_buffer["wind_speed_2d"])

    fig = go.Figure()
    fig.add_trace(
        go.Barpolar(
            r=speeds,
            theta=angles,
            name="Wind Speed",
            marker=dict(
                color=speeds,
                colorscale="Viridis",
                colorbar=dict(
                    title="m/s",
                    titleside="right",
                    thickness=15,
                    len=0.5,
                    outlinewidth=0,
                ),
                cmin=0,
                cmax=max(speeds) + 0.5,
            ),
            hovertemplate="Speed: %{r:.1f} m/s<br>Direction: %{theta:.1f}°",
        )
    )

    # Apply dark theme to wind rose
    fig.update_layout(
        title="Wind Rose",
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="white"),
        polar=dict(
            radialaxis=dict(
                range=[0, max(speeds) + 1], gridcolor="#333", linecolor="#333"
            ),
            angularaxis=dict(
                direction="clockwise", rotation=90, gridcolor="#333", linecolor="#333"
            ),
            bgcolor="#0e1117",
        ),
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        height=450,
    )
    return fig


def start_receiver():
    """Start the UDP receiver if not already running."""
    if st.session_state.receiver is None:
        st.session_state.receiver = DashboardUDPReceiver()
        receiver_thread = threading.Thread(
            target=st.session_state.receiver.start, daemon=True
        )

        # Add Streamlit script context to the thread
        ctx = get_script_run_ctx()
        add_script_run_ctx(receiver_thread, ctx)

        receiver_thread.start()


def create_dark_theme_plot(fig):
    """Apply dark theme to a plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="white"),
        xaxis=dict(
            gridcolor="#333",
            zerolinecolor="#333",
        ),
        yaxis=dict(
            gridcolor="#333",
            zerolinecolor="#333",
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=350,
    )
    return fig


def toggle_pause():
    """Toggle the pause state."""
    st.session_state.paused = not st.session_state.paused


def main():
    # Create title with control buttons
    col_title, col_status, col_controls = st.columns([0.6, 0.25, 0.15])
    with col_title:
        st.title("Live Weather Dashboard")

    with col_status:
        info_placeholder = st.empty()

    with col_controls:
        cols = st.columns(2)
        # Add pause/resume button
        pause_label = "▶️ Resume" if st.session_state.paused else "⏸️ Pause"
        if cols[0].button(pause_label):
            toggle_pause()

        # Add refresh button - wrapped in try/except to handle the "Bad 'setIn' index" error
        try:
            if cols[1].button("🔄 Refresh"):
                # Clean refresh without state modification
                pass
        except Exception:
            pass

    # Show update info
    with info_placeholder:
        status = (
            "Paused"
            if st.session_state.paused
            else f"Updating at {st.session_state.update_interval} Hz"
        )
        st.info(f"Display Status: {status} (Data collection ~9 Hz)")

    # Automatically start the receiver when the app loads
    if st.session_state.receiver is None:
        start_receiver()

    # Create layout with columns - make wind rose wider
    col_wind_rose, col_metrics = st.columns([0.7, 0.3])

    # Initialize containers once
    if st.session_state.plot_containers["wind_rose"] is None:
        with col_wind_rose:
            st.session_state.plot_containers["wind_rose"] = st.empty()

        with col_metrics:
            # Create individual metric placeholders
            st.subheader("Current Weather Metrics")
            st.session_state.plot_containers["metric_wind_speed"] = st.empty()
            st.session_state.plot_containers["metric_wind_direction"] = st.empty()
            st.session_state.plot_containers["metric_temperature"] = st.empty()
            st.session_state.plot_containers["metric_pressure"] = st.empty()
            st.session_state.plot_containers["metric_humidity"] = st.empty()

        # Create even columns for temperature and pressure history
        col_temp, col_press = st.columns(2)
        with col_temp:
            st.session_state.plot_containers["temperature"] = st.empty()
        with col_press:
            st.session_state.plot_containers["pressure"] = st.empty()

    # Update function - fixed at 1 Hz
    @st.fragment(
        run_every=None if st.session_state.paused else st.session_state.update_interval
    )
    def update_dashboard():
        # Wind rose plot
        wind_rose = create_wind_rose()
        if wind_rose:
            st.session_state.plot_containers["wind_rose"].plotly_chart(
                wind_rose, use_container_width=True
            )

        # Current metrics - update each metric individually
        if len(st.session_state.data_buffer["timestamp"]) > 0:
            st.session_state.plot_containers["metric_wind_speed"].metric(
                "Wind Speed (2D)",
                f"{list(st.session_state.data_buffer['wind_speed_2d'])[-1]:.1f} m/s",
            )
            st.session_state.plot_containers["metric_wind_direction"].metric(
                "Wind Direction",
                f"{list(st.session_state.data_buffer['azimuth'])[-1]:.1f}°",
            )
            st.session_state.plot_containers["metric_temperature"].metric(
                "Temperature",
                f"{list(st.session_state.data_buffer['temperature'])[-1]:.1f}°C",
            )
            st.session_state.plot_containers["metric_pressure"].metric(
                "Pressure",
                f"{list(st.session_state.data_buffer['pressure'])[-1]:.1f} Pa",
            )
            st.session_state.plot_containers["metric_humidity"].metric(
                "Humidity", f"{list(st.session_state.data_buffer['humidity'])[-1]:.1f}%"
            )

        # Temperature plot
        if len(st.session_state.data_buffer["timestamp"]) > 0:
            temp_df = pd.DataFrame(
                {
                    "Time": list(st.session_state.data_buffer["timestamp"]),
                    "Temperature": list(st.session_state.data_buffer["temperature"]),
                    "Sonic Temperature": list(
                        st.session_state.data_buffer["sonic_temp"]
                    ),
                }
            )
            fig_temp = px.line(
                temp_df,
                x="Time",
                y=["Temperature", "Sonic Temperature"],
                title="Temperature History",
            )
            fig_temp = create_dark_theme_plot(fig_temp)
            st.session_state.plot_containers["temperature"].plotly_chart(
                fig_temp, use_container_width=True
            )

        # Pressure plot
        if len(st.session_state.data_buffer["timestamp"]) > 0:
            press_df = pd.DataFrame(
                {
                    "Time": list(st.session_state.data_buffer["timestamp"]),
                    "Pressure": list(st.session_state.data_buffer["pressure"]),
                }
            )
            fig_press = px.line(
                press_df, x="Time", y="Pressure", title="Pressure History"
            )
            fig_press = create_dark_theme_plot(fig_press)
            st.session_state.plot_containers["pressure"].plotly_chart(
                fig_press, use_container_width=True
            )

    update_dashboard()


if __name__ == "__main__":
    main()
