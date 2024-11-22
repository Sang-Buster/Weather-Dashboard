import streamlit as st
import plotly.express as px


def correlation_plot_component():
    # Load the data
    df = st.session_state.filtered_df

    # Calculate correlation matrix
    variables_to_correlate = [
        "u_m_s",
        "v_m_s",
        "w_m_s",
        "2dSpeed_m_s",
        "3DSpeed_m_s",
        "Temp_C",
        "Hum_RH",
        "Press_Pa",
        "SonicTemp_C",
        "Azimuth_deg",
        "Elev_deg",
    ]

    correlation_matrix = df[variables_to_correlate].corr()

    # Create correlation heatmap using plotly
    fig = px.imshow(
        correlation_matrix,
        color_continuous_scale="RdYlBu_r",
        aspect="auto",
        labels={
            "u_m_s": "U Wind",
            "v_m_s": "V Wind",
            "w_m_s": "W Wind",
            "2dSpeed_m_s": "2D Wind Speed",
            "3DSpeed_m_s": "3D Wind Speed",
            "Temp_C": "Temperature",
            "Hum_RH": "Relative Humidity",
            "Press_Pa": "Pressure",
            "SonicTemp_C": "Sonic Temperature",
            "Azimuth_deg": "Wind Direction",
            "Elev_deg": "Elevation Angle",
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
    for i in range(len(correlation_matrix.columns)):
        for j in range(len(correlation_matrix.index)):
            fig.add_annotation(
                x=i,
                y=j,
                text=f"{correlation_matrix.iloc[j, i]:.2f}",
                showarrow=False,
                font=dict(
                    color="black"
                    if abs(correlation_matrix.iloc[j, i]) < 0.7
                    else "white",
                    size=8,
                ),
            )

    st.plotly_chart(fig, use_container_width=True)
