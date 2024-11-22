import streamlit as st
import plotly.express as px


def scatter_plot_component():
    # Load the data
    df = st.session_state.filtered_df

    # Define available variables for plotting
    numeric_columns = [
        "2dSpeed_m_s",
        "3DSpeed_m_s",
        "u_m_s",
        "v_m_s",
        "w_m_s",
        "Azimuth_deg",
        "Elev_deg",
        "Press_Pa",
        "Temp_C",
        "Hum_RH",
        "SonicTemp_C",
    ]

    # Create plot placeholder
    plot_placeholder = st.empty()

    # Create initial scatter plot
    fig = px.scatter(
        df,
        x="Temp_C",
        y="2dSpeed_m_s",
        color="Hum_RH",
        labels={
            "Temp_C": "Temperature (°C)",
            "2dSpeed_m_s": "Wind Speed (m/s)",
            "Hum_RH": "Relative Humidity (%)",
        },
        color_continuous_scale="viridis",
        opacity=0.5,
    )

    # Update layout
    fig.update_layout(
        width=600,
        height=680,
        title={
            "text": "Wind Speed vs Temperature (colored by Relative Humidity)",
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        hovermode="closest",
        coloraxis_colorbar_title="Relative Humidity (%)",
    )

    # Display the plot in the placeholder
    plot_placeholder.plotly_chart(fig, use_container_width=True)

    # Create three columns for selectboxes below the plot
    col1, col2, col3 = st.columns(3)

    with col1:
        x_var = st.selectbox(
            "Select X-axis variable:",
            options=numeric_columns,
            index=numeric_columns.index("Temp_C"),
        )

    with col2:
        y_var = st.selectbox(
            "Select Y-axis variable:",
            options=numeric_columns,
            index=numeric_columns.index("2dSpeed_m_s"),
        )

    with col3:
        color_var = st.selectbox(
            "Select Color variable:",
            options=numeric_columns,
            index=numeric_columns.index("Hum_RH"),
        )

    # Update plot if selections change
    if x_var != "Temp_C" or y_var != "2dSpeed_m_s" or color_var != "Hum_RH":
        updated_fig = px.scatter(
            df,
            x=x_var,
            y=y_var,
            color=color_var,
            labels={x_var: f"{x_var}", y_var: f"{y_var}", color_var: f"{color_var}"},
            color_continuous_scale="viridis",
            opacity=0.5,
        )

        updated_fig.update_layout(
            width=600,
            height=680,
            title={
                "text": f"{y_var} vs {x_var} (colored by {color_var})",
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            hovermode="closest",
            coloraxis_colorbar_title=f"{color_var}",
        )

        plot_placeholder.plotly_chart(updated_fig, use_container_width=True)
