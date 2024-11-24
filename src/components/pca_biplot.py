import streamlit as st
import plotly.graph_objects as go
import json
import numpy as np


def pca_biplot_components():
    try:
        # Load PCA data from JSON
        with open("src/data/pca_data.json", "r") as f:
            pca_data = json.load(f)

        biplot_data = pca_data["biplot_data"]
        features = biplot_data["features"]
        pc_coordinates = np.array(biplot_data["pc_coordinates"])
        explained_variance_3d = biplot_data["explained_variance_3d"]

        # Create the 3D scatter plot
        fig = go.Figure()

        # Add loading vectors
        scaling_factor = 3  # Adjust this to change the length of loading vectors
        for i, feature in enumerate(features):
            fig.add_trace(
                go.Scatter3d(
                    x=[0, pc_coordinates[i, 0] * scaling_factor],
                    y=[0, pc_coordinates[i, 1] * scaling_factor],
                    z=[0, pc_coordinates[i, 2] * scaling_factor],
                    mode="lines+text",
                    line=dict(color="red", width=3),
                    text=["", feature],
                    textposition="top center",
                    textfont=dict(color="red", size=12),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        # Update layout
        fig.update_layout(
            title={
                "text": "3D PCA Biplot",
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            scene=dict(
                xaxis_title=f"PC1 ({explained_variance_3d[0]:.1%} explained var)",
                yaxis_title=f"PC2 ({explained_variance_3d[1]:.1%} explained var)",
                zaxis_title=f"PC3 ({explained_variance_3d[2]:.1%} explained var)",
                aspectmode="cube",
            ),
            width=600,
            height=600,
            showlegend=True,
            # ... rest of your layout code ...
        )

        # ... rest of your existing layout code ...

        st.plotly_chart(fig, use_container_width=True)

    except FileNotFoundError:
        st.error("PCA data file not found. Please run the data analysis first.")
    except Exception as e:
        st.error(f"Error loading PCA biplot: {str(e)}")
