import streamlit as st
import plotly.express as px
import json


def correlation_plot_component():
    # Load the correlation data from JSON
    try:
        with open("src/data/correlation_data.json", "r") as f:
            correlation_data = json.load(f)

        # Convert the nested dict to a list of lists for plotly
        variables = list(correlation_data.keys())
        correlation_matrix = [
            [correlation_data[var1][var2] for var2 in variables] for var1 in variables
        ]

        # Create correlation heatmap using plotly
        fig = px.imshow(
            correlation_matrix,
            x=variables,
            y=variables,
            color_continuous_scale="RdYlBu_r",
            aspect="auto",
            labels={
                "3DSpeed_m_s": "3D Wind Speed",
                "Azimuth_deg": "Wind Direction",
                "Elev_deg": "Elevation Angle",
                "Press_Pa": "Pressure",
                "Temp_C": "Temperature",
                "Hum_RH": "Relative Humidity",
            },
            color_continuous_midpoint=0,
            range_color=[-1, 1],
        )

        # Update layout
        fig.update_layout(
            width=800,
            height=800,
            title={
                "text": "Correlation Plot",
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            xaxis_title="",
            yaxis_title="",
            xaxis={"tickangle": 45},
        )

        # Add correlation values as text annotations
        for i in range(len(variables)):
            for j in range(len(variables)):
                value = correlation_matrix[j][i]
                fig.add_annotation(
                    x=i,
                    y=j,
                    text=f"{value:.2f}",
                    showarrow=False,
                    font=dict(
                        color="black" if abs(value) < 0.7 else "white",
                        size=8,
                    ),
                )

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading correlation data: {e}")
