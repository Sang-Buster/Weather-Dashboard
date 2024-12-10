import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


def celsius_to_fahrenheit(temp_c):
    """Convert Celsius to Fahrenheit"""
    return (temp_c * 9 / 5) + 32


def calculate_dew_point(temp, rel_humidity):
    """Calculate dew point using the Magnus formula"""
    a = 17.27
    b = 237.7
    alpha = ((a * temp) / (b + temp)) + np.log(rel_humidity / 100.0)
    return (b * alpha) / (a - alpha)


@st.fragment
def environmental_time_series_component():
    # Check if filtered_df exists and is not None
    if "filtered_df" not in st.session_state or st.session_state.filtered_df is None:
        st.warning("Please select a date range first.")
        return

    # Make an explicit copy of the filtered DataFrame
    df = st.session_state.filtered_df.copy()

    # Calculate dew point in Celsius
    df.loc[:, "DewPoint_C"] = calculate_dew_point(df["Temp_C"], df["Hum_RH"])

    # Convert temperatures to Fahrenheit
    df.loc[:, "Temp_F"] = celsius_to_fahrenheit(df["Temp_C"])
    df.loc[:, "SonicTemp_F"] = celsius_to_fahrenheit(df["SonicTemp_C"])
    df.loc[:, "DewPoint_F"] = celsius_to_fahrenheit(df["DewPoint_C"])

    # Updated default variables to include humidity
    default_vars = ["SonicTemp_F", "Temp_F", "DewPoint_F", "Hum_RH"]
    fig = create_env_plot(df, default_vars)

    # Display the plot
    plot_placeholder = st.empty()
    plot_placeholder.plotly_chart(fig, use_container_width=True)

    # UI elements below the plot
    env_options = ["SonicTemp_F", "Temp_F", "DewPoint_F", "Hum_RH", "Press_Pa"]
    selected_vars = st.multiselect(
        "Select environmental variables to display:",
        options=env_options,
        default=default_vars,
    )

    # If selections change, update the plot
    if selected_vars != default_vars:
        updated_fig = create_env_plot(df, selected_vars)
        plot_placeholder.plotly_chart(updated_fig, use_container_width=True)


def create_env_plot(df, selected_vars):
    # Downsample data more efficiently - using iloc
    df_plot = df.iloc[::10]

    # Define color scheme for each variable
    color_scheme = {
        "SonicTemp_F": dict(
            fillcolor="rgba(135, 206, 235, 0.3)",  # Light sky blue
            line_color="rgba(135, 206, 235, 0.8)",
        ),
        "Temp_F": dict(
            fillcolor="rgba(144, 238, 144, 0.3)",  # Light green
            line_color="rgba(144, 238, 144, 0.8)",
        ),
        "DewPoint_F": dict(
            fillcolor="rgba(221, 160, 221, 0.3)",  # Light purple/plum
            line_color="rgba(221, 160, 221, 0.8)",
        ),
        "Hum_RH": dict(
            fillcolor="rgba(255, 255, 180, 0.3)",  # Light yellow
            line_color="rgba(255, 255, 180, 0.8)",
        ),
        "Press_Pa": dict(
            fillcolor="rgba(205, 133, 63, 0.3)",  # Light brown
            line_color="rgba(205, 133, 63, 0.8)",
        ),
    }

    # Create the plot with optimized settings
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for var in selected_vars:
        trace_data = {
            "x": df_plot["tNow"],
            "y": df_plot[var],
            "name": var,
            "mode": "lines",  # Remove markers for better performance
            "line": dict(
                color=color_scheme[var]["line_color"],
                shape="linear",  # Use linear interpolation
                width=1,  # Thinner lines for better performance
            ),
        }

        # Only add fill if specifically needed
        if var in ["SonicTemp_F", "Temp_F", "DewPoint_F", "Hum_RH", "Press_Pa"]:
            trace_data["fill"] = "tozeroy"
            trace_data["fillcolor"] = color_scheme[var]["fillcolor"]

        fig.add_trace(go.Scatter(**trace_data), secondary_y=(var == "Hum_RH"))

    # Optimize layout
    fig.update_layout(
        title={
            "text": "Environmental Conditions",
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        xaxis_title="Time",
        yaxis_title="Temperature (°F)",
        yaxis2=dict(
            title="Relative Humidity (%)",
            overlaying="y",
            side="right",
            range=[0, 100],
        ),
        width=520,
        height=520,
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
