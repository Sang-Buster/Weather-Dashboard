import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def create_wind_rose(df):
    # Make an explicit copy at the start
    df = df.copy()

    # Convert wind speed from m/s to mph
    df.loc[:, "2dSpeed_mph"] = df["2dSpeed_m_s"] * 2.23694

    # Define direction bins
    dir_bins = np.arange(0, 361, 22.5)
    dir_labels = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]

    # Define speed bins in mph
    speed_bins = [0, 4.5, 9, 13.5, 18, 22.5, np.inf]
    speed_labels = ["0-4.5", "4.5-9", "9-13.5", "13.5-18", "18-22.5", "22.5+"]

    # Categorize data
    df.loc[:, "dir_cat"] = pd.cut(
        df["Azimuth_deg"],
        bins=dir_bins,
        labels=dir_labels,
        include_lowest=True,
        ordered=False,
    )
    df.loc[:, "speed_cat"] = pd.cut(
        df["2dSpeed_mph"],
        bins=speed_bins,
        labels=speed_labels,
        include_lowest=True,
        ordered=False,
    )

    # Count occurrences and calculate percentages
    wind_data = (
        df.groupby(["dir_cat", "speed_cat"], observed=True).size().unstack(fill_value=0)
    )
    total_count = wind_data.sum().sum()
    wind_percentages = wind_data / total_count * 100

    # Create wind rose
    fig = go.Figure()

    colors = [
        "#440154",
        "#404387",
        "#29788E",
        "#22A784",
        "#79D151",
        "#FDE724",
    ]  # Viridis-like color sequence

    for i, speed_cat in enumerate(speed_labels):
        fig.add_trace(
            go.Barpolar(
                r=wind_percentages[speed_cat],
                theta=dir_labels,
                name=speed_cat,
                marker_color=colors[i],
                marker_line_width=1,
                opacity=0.8,
                hovertemplate="Direction: %{theta}<br>"
                + "Speed: "
                + speed_cat
                + " mph<br>"
                + "Percentage: %{r:.1f}%<extra></extra>",
            )
        )

    fig.update_layout(
        title={
            "text": "Wind Rose Diagram",
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        font_size=12,
        legend_font_size=10,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, wind_percentages.max().max()],
                ticksuffix="%",
                tickmode="array",
                tickvals=np.arange(0, wind_percentages.max().max(), 5),
                ticktext=[
                    f"{i}%" for i in range(0, int(wind_percentages.max().max()), 5)
                ],
            ),
            angularaxis=dict(direction="clockwise", rotation=90),
            bgcolor="rgba(0,0,0,0)",  # Set polar area background to transparent
        ),
        width=620,
        height=620,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5
        ),
    )

    return fig


def create_wind_rose_over_time(df):
    # Convert wind speed from m/s to mph
    df["2dSpeed_mph"] = df["2dSpeed_m_s"] * 2.23694  # 1 m/s = 2.23694 mph

    # Define direction bins
    dir_bins = np.arange(0, 361, 22.5)
    dir_labels = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]

    # Define speed bins in mph
    speed_bins = [0, 4.5, 9, 13.5, 18, 22.5, np.inf]
    speed_labels = ["0-4.5", "4.5-9", "9-13.5", "13.5-18", "18-22.5", "22.5+"]

    # Categorize data
    df["dir_cat"] = pd.cut(
        df["Azimuth_deg"],
        bins=dir_bins,
        labels=dir_labels,
        include_lowest=True,
        ordered=False,
    )
    df["speed_cat"] = pd.cut(
        df["2dSpeed_mph"],
        bins=speed_bins,
        labels=speed_labels,
        include_lowest=True,
        ordered=False,
    )

    # Count occurrences and calculate percentages
    wind_data = (
        df.groupby(["dir_cat", "speed_cat"], observed=True).size().unstack(fill_value=0)
    )
    total_count = wind_data.sum().sum()
    wind_percentages = wind_data / total_count * 100

    # Create wind rose
    fig = go.Figure()

    colors = [
        "#440154",
        "#404387",
        "#29788E",
        "#22A784",
        "#79D151",
        "#FDE724",
    ]  # Viridis-like color sequence

    for i, speed_cat in enumerate(speed_labels):
        fig.add_trace(
            go.Barpolar(
                r=wind_percentages[speed_cat],
                theta=dir_labels,
                name=speed_cat,
                marker_color=colors[i],
                marker_line_width=1,
                opacity=0.8,
                hovertemplate="Direction: %{theta}<br>"
                + "Speed: "
                + speed_cat
                + " mph<br>"
                + "Percentage: %{r:.1f}%<extra></extra>",
            )
        )

    fig.update_layout(
        title={
            "text": "Wind Rose Diagram",
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        font_size=12,
        legend_font_size=10,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, wind_percentages.max().max()],
                ticksuffix="%",
                tickmode="array",
                tickvals=np.arange(0, wind_percentages.max().max(), 5),
                ticktext=[
                    f"{i}%" for i in range(0, int(wind_percentages.max().max()), 5)
                ],
            ),
            angularaxis=dict(direction="clockwise", rotation=90),
            bgcolor="rgba(0,0,0,0)",  # Set polar area background to transparent
        ),
        width=620,
        height=620,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5
        ),
    )

    return fig


def wind_rose_component():
    # Check if filtered_df exists in session state
    if "filtered_df" not in st.session_state:
        st.warning("Please select a date range first.")
        return

    # Make an explicit copy
    df = st.session_state.filtered_df.copy()

    # Ensure 'tNow' is a datetime column
    df.loc[:, "tNow"] = pd.to_datetime(df["tNow"])

    # Check if start and end dates are the same
    start_date = df["tNow"].min().date()
    end_date = df["tNow"].max().date()

    if start_date == end_date:
        # For a single day, create a 24-hour wind rose
        fig = create_wind_rose(df)
    else:
        # For multiple days, create a wind rose for the entire period
        fig = create_wind_rose_over_time(df)

    st.plotly_chart(fig, use_container_width=True)
