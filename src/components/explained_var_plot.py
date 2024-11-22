import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


def pca_explained_variance_component():
    # Get data from session state
    df = st.session_state.filtered_df

    # Define features for PCA
    features = [
        "u_m_s",
        "v_m_s",
        "w_m_s",
        "2dSpeed_m_s",
        "Azimuth_deg",
        "Elev_deg",
        "Press_Pa",
        "Temp_C",
        "Hum_RH",
        "SonicTemp_C",
    ]

    # Standardize the features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[features])

    # Perform PCA
    pca = PCA()
    pca.fit_transform(scaled_features)

    # Calculate explained variance ratio
    explained_variance_ratio = pca.explained_variance_ratio_
    cumulative_variance_ratio = np.cumsum(explained_variance_ratio)

    # Create DataFrame for plotting
    variance_df = pd.DataFrame(
        {
            "Component": [f"PC{i+1}" for i in range(len(explained_variance_ratio))],
            "Individual": explained_variance_ratio * 100,
            "Cumulative": cumulative_variance_ratio * 100,
        }
    )

    # Create the plot
    fig = px.line(
        variance_df,
        x="Component",
        y="Cumulative",
        markers=True,
        labels={"Cumulative": "Explained Variance (%)"},
        title="PCA Explained Variance Ratio",
    )

    # Add bar chart for individual explained variance
    fig.add_bar(
        x=variance_df["Component"],
        y=variance_df["Individual"],
        name="Individual",
        opacity=0.5,
    )

    # Add 80% reference line
    fig.add_hline(
        y=80,
        line_dash="dash",
        line_color="red",
        annotation_text="80% Threshold",
        annotation_position="right",
    )

    # Add annotations for incremental variance
    for i in range(len(explained_variance_ratio) - 1):
        increment = explained_variance_ratio[i + 1] * 100
        fig.add_annotation(
            x=variance_df["Component"][i + 1],
            y=variance_df["Cumulative"][i],
            text=f"+{increment:.1f}%",
            showarrow=False,
            xshift=-30,
            yshift=30,
            font=dict(size=15),
        )

    # Update layout
    fig.update_layout(
        yaxis_title="Explained Variance (%)",
        showlegend=False,
        hovermode="x unified",
        width=600,
        height=600,
        margin=dict(t=30, b=0),
        title={
            "text": "PCA Explained Variance Ratio",
            "x": 0.5,  # Center the title
            "xanchor": "center",
            "yanchor": "top",
        },
    )

    # Add grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")

    st.plotly_chart(fig, use_container_width=True)
