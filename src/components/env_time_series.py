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
    # Make an explicit copy of the filtered DataFrame
    df = st.session_state.filtered_df.copy()

    # Calculate dew point in Celsius
    df.loc[:, "DewPoint_C"] = calculate_dew_point(df["Temp_C"], df["Hum_RH"])

    # Convert temperatures to Fahrenheit
    df.loc[:, "Temp_F"] = celsius_to_fahrenheit(df["Temp_C"])
    df.loc[:, "SonicTemp_F"] = celsius_to_fahrenheit(df["SonicTemp_C"])
    df.loc[:, "DewPoint_F"] = celsius_to_fahrenheit(df["DewPoint_C"])

    # Create the initial plot
    fig = create_env_plot(df, ["SonicTemp_F", "Temp_F", "Hum_RH"])

    # Display the plot
    plot_placeholder = st.empty()
    plot_placeholder.plotly_chart(fig, use_container_width=True)

    # UI elements below the plot
    env_options = ["SonicTemp_F", "Temp_F", "DewPoint_F", "Hum_RH", "Press_Pa"]
    selected_vars = st.multiselect(
        "Select environmental variables to display:",
        options=env_options,
        default=["SonicTemp_F", "Temp_F", "DewPoint_F"],
    )

    # If selections change, update the plot
    if selected_vars != ["SonicTemp_F", "Temp_F", "Hum_RH"]:
        updated_fig = create_env_plot(df, selected_vars)
        plot_placeholder.plotly_chart(updated_fig, use_container_width=True)


def create_env_plot(df, selected_vars):
    # Create the plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for var in selected_vars:
        if var == "Hum_RH":
            # Plot humidity on secondary y-axis
            fig.add_trace(
                go.Scatter(x=df["tNow"], y=df[var], name=var, fill="tozeroy"),
                secondary_y=True,
            )
        else:
            # Plot temperature variables on primary y-axis
            fig.add_trace(
                go.Scatter(x=df["tNow"], y=df[var], name=var, fill="tozeroy"),
                secondary_y=False,
            )

    # Update layout
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
    )

    return fig
