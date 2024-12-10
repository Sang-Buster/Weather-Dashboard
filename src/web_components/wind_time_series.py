import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


@st.fragment
def wind_time_series_component():
    # Check if filtered_df exists in session state
    if "filtered_df" not in st.session_state:
        st.warning("Please select a date range first.")
        return

    # Make an explicit copy of the filtered DataFrame
    df = st.session_state.filtered_df.copy()

    # Ensure tNow is a datetime index
    df.loc[:, "tNow"] = pd.to_datetime(df["tNow"])
    df.set_index("tNow", inplace=True)

    # Sort the DataFrame by the time index
    df.sort_index(inplace=True)

    # Convert wind speed columns from m/s to mph
    speed_columns = ["2dSpeed_m_s", "3DSpeed_m_s", "u_m_s", "v_m_s", "w_m_s"]
    for col in speed_columns:
        df.loc[:, col.replace("m_s", "mph")] = df[col] * 2.23694  # Convert m/s to mph

    # Define average wind direction interval_map
    interval_map = {
        "10 minutes": pd.Timedelta(minutes=10),
        "30 minutes": pd.Timedelta(minutes=30),
        "1 hour": pd.Timedelta(hours=1),
        "2 hour": pd.Timedelta(hours=2),
        "3 hour": pd.Timedelta(hours=3),
    }

    # Define average gust wind speed interval_map
    gust_interval_map = {
        "3 seconds": "3s",
        "5 seconds": "5s",
        "10 seconds": "10s",
        "20 seconds": "20s",
        "30 seconds": "30s",
        "1 min": "1min",
        "2 min": "2min",
        "3 min": "3min",
    }

    # Calculate average gust wind speed (default to 3min)
    df.loc[:, "GustSpeed_mph"] = df["2dSpeed_mph"].rolling(window="3min").max()

    # Update speed_options to include gust speed
    speed_options = [col.replace("m_s", "mph") for col in speed_columns] + [
        "GustSpeed_mph"
    ]

    # Create the initial plot
    fig = create_wind_plot(
        df,
        ["2dSpeed_mph", "3DSpeed_mph", "GustSpeed_mph"],
        "30 minutes",
        interval_map,
        "3min",
    )

    # Display the plot
    plot_placeholder = st.empty()
    plot_placeholder.plotly_chart(fig, use_container_width=True)

    # UI elements below the plot
    col1, col2 = st.columns(2)

    with col1:
        selected_speeds = st.multiselect(
            "Select wind speed components to display:",
            options=speed_options,
            default=["2dSpeed_mph", "3DSpeed_mph", "GustSpeed_mph"],
        )

    with col2:
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            arrow_interval = st.selectbox(
                "Select interval for average wind direction arrows:",
                options=list(interval_map.keys()),
                index=1,  # Default to 30 minutes
            )
        with col2_2:
            gust_wind_interval = st.selectbox(
                "Select interval for gust wind speed:",
                options=list(gust_interval_map.keys()),
                index=7,  # Default to 3 min
            )

    # If selections change, update the plot
    if (
        selected_speeds != ["2dSpeed_mph", "3DSpeed_mph", "GustSpeed_mph"]
        or arrow_interval != "30 minutes"
        or gust_wind_interval != "3 min"
    ):
        # Recalculate gust wind speed based on selected interval
        df.loc[:, "GustSpeed_mph"] = (
            df["2dSpeed_mph"]
            .rolling(window=gust_interval_map[gust_wind_interval])
            .max()
        )

        updated_fig = create_wind_plot(
            df,
            selected_speeds,
            arrow_interval,
            interval_map,
            gust_interval_map[gust_wind_interval],
        )
        plot_placeholder.plotly_chart(updated_fig, use_container_width=True)


def create_wind_plot(df, selected_speeds, arrow_interval, interval_map, gust_interval):
    # Downsample data more efficiently - using iloc
    df_plot = df.iloc[::5]  # Much faster than .copy()

    # Create the plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces for selected wind speed components
    for speed in selected_speeds:
        fig.add_trace(
            go.Scatter(
                x=df_plot.index,
                y=df_plot[speed],
                name=speed,
                mode="lines",  # Remove markers for better performance
                line=dict(
                    width=1,  # Thinner lines for better performance
                    shape="linear",  # Use linear interpolation
                ),
            ),
            secondary_y=False,
        )

    # Calculate the y-position for direction markers
    y_pos = df_plot[selected_speeds].max().max() * 1.1

    # Resample data based on the selected arrow_interval
    interval = interval_map[arrow_interval]

    # Create a new DataFrame with only the columns we need
    df_direction = pd.DataFrame(df["Azimuth_deg"].astype(float))

    # Calculate the average direction using circular mean
    def circular_mean(angles):
        angles_rad = np.radians(angles)
        x = np.mean(np.cos(angles_rad))
        y = np.mean(np.sin(angles_rad))
        mean_angle = np.degrees(np.arctan2(y, x)) % 360
        return mean_angle

    # Resample the data and calculate the average direction
    df_resampled = df_direction.resample(interval).agg({"Azimuth_deg": circular_mean})

    # Add direction arrows with optimized settings
    fig.add_trace(
        go.Scatter(
            x=df_resampled.index,
            y=[y_pos] * len(df_resampled),
            mode="markers",
            marker=dict(
                symbol="arrow",
                size=12,  # Slightly smaller markers
                angle=(df_resampled["Azimuth_deg"] + 180) % 360,
                line=dict(width=1, color="white"),
                color="rgba(255, 255, 255, 0.8)",
            ),
            name=f"Wind Direction ({arrow_interval})",
            hovertemplate="<br>Time: %{x}<br>Direction: %{text:.1f}°",
            text=df_resampled["Azimuth_deg"],
        ),
        secondary_y=False,
    )

    # Update layout with optimized settings
    fig.update_layout(
        title={
            "text": "Wind Speed and Direction",
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        xaxis_title="Time",
        yaxis=dict(
            title="Wind Speed (mph)",
            side="right",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5),
        hovermode="x unified",
        # Performance optimizations
        uirevision=True,  # Preserve UI state on updates
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    # Additional performance optimizations
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")

    return fig
