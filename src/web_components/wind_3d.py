import streamlit as st
import plotly.graph_objects as go
import numpy as np


def ms_to_mph(speed_ms):
    """Convert meters per second to miles per hour."""
    return speed_ms * 2.23694


@st.fragment
def wind_3d_component():
    """Create 3D surface plot of wind speed over time and direction using Plotly."""

    # Get the filtered data from session state
    if "filtered_df" not in st.session_state:
        st.warning("Please select a date range first.")
        return

    combined_df = st.session_state.filtered_df

    # Check if required columns exist
    required_columns = ["3DSpeed_m_s", "Azimuth_deg", "tNow"]
    if not all(col in combined_df.columns for col in required_columns):
        st.error("Required columns are missing from the dataset.")
        return

    # Convert wind speed to mph
    wind_speed_mph = ms_to_mph(combined_df["3DSpeed_m_s"])

    # Create direction and time meshgrid with reversed time
    dir_bins = np.linspace(0, 360, 73)  # 5-degree bins
    time_bins = np.linspace(len(combined_df) - 1, 0, 100)  # Reversed time bins

    Dir, Time = np.meshgrid(dir_bins, time_bins)
    Speed = np.zeros_like(Dir)

    # For each time bin, interpolate speeds across directions
    for i, t in enumerate(time_bins):
        idx = int(round(t))
        if idx >= len(combined_df):
            idx = len(combined_df) - 1

        actual_dir = combined_df["Azimuth_deg"].iloc[idx]
        actual_speed = wind_speed_mph.iloc[idx]

        # Gaussian smoothing
        sigma = 15  # Width of gaussian in degrees
        dir_diff = np.minimum(
            np.abs(Dir[i] - actual_dir), np.abs(Dir[i] - (actual_dir + 360))
        )
        dir_diff = np.minimum(dir_diff, np.abs(Dir[i] - (actual_dir - 360)))
        Speed[i] = actual_speed * np.exp(-(dir_diff**2) / (2 * sigma**2))

    # Get time labels for x-axis (reversed)
    num_ticks = min(10, len(combined_df) // 100)
    tick_indices = np.linspace(len(combined_df) - 1, 0, num_ticks)  # Reversed indices
    tick_labels = [
        combined_df["tNow"].iloc[int(idx)].strftime("%Y-%m-%d %H:%M")
        for idx in tick_indices
    ]

    # Create customdata array for hover template
    customdata = np.zeros_like(Dir, dtype="object")
    for i, t in enumerate(time_bins):
        idx = int(round(t))
        if idx >= len(combined_df):
            idx = len(combined_df) - 1
        time_str = combined_df["tNow"].iloc[idx].strftime("%Y-%m-%d %H:%M")
        customdata[i, :] = time_str

    # Create the surface plot using Plotly
    fig = go.Figure(
        data=[
            go.Surface(
                x=Time,
                y=Dir,
                z=Speed,
                colorscale="Viridis",
                showscale=False,  # Hide the color bar
                hovertemplate=(
                    "Time: %{customdata}<br>"
                    "Direction: %{y:.0f}°<br>"
                    "Wind Speed: %{z:.1f} mph<br>"
                    "<extra></extra>"
                ),
                customdata=customdata,
            )
        ]
    )

    # Update layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(
                title="Time",
                ticktext=tick_labels,
                tickvals=tick_indices,
                autorange="reversed",  # This ensures the axis stays reversed
            ),
            yaxis=dict(
                title="Wind Direction",
                ticktext=["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"],
                tickvals=np.arange(0, 361, 45),
            ),
            zaxis=dict(title="Wind Speed (mph)"),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
        ),
        title=dict(
            text="3D Wind Pattern",
            x=0.5,  # Center the title
            xanchor="center",
            y=0.95,
        ),
        margin=dict(t=0, b=0, l=0, r=0),
        height=700,
    )

    # Display the plot
    st.plotly_chart(fig, use_container_width=True)
