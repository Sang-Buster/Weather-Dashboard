import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


def pca_biplot_components():
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
    pc_scores = pca.fit_transform(scaled_features)

    # Get loadings
    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)

    # Create DataFrame with PC scores (first 3 components)
    pc_df = pd.DataFrame(pc_scores[:, :3], columns=["PC1", "PC2", "PC3"])

    # Determine dominant PC for each point
    pc_abs = np.abs(pc_scores[:, :3])
    dominant_pc = np.argmax(pc_abs, axis=1)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]  # Blue, Orange, Green for PC1, PC2, PC3
    point_colors = [colors[pc] for pc in dominant_pc]

    # Create the 3D scatter plot of PC scores
    fig = go.Figure()

    # Add scatter points with color based on dominant PC
    fig.add_trace(
        go.Scatter3d(
            x=pc_df["PC1"],
            y=pc_df["PC2"],
            z=pc_df["PC3"],
            mode="markers",
            marker=dict(size=4, opacity=0.6, color=point_colors),
            hovertemplate="<br>".join(
                ["PC1: %{x:.2f}", "PC2: %{y:.2f}", "PC3: %{z:.2f}", "<extra></extra>"]
            ),
            showlegend=False,  # Hide from legend
        )
    )

    # Add loading vectors
    scaling_factor = 3  # Adjust this to change the length of loading vectors
    for i, feature in enumerate(features):
        fig.add_trace(
            go.Scatter3d(
                x=[0, loadings[i, 0] * scaling_factor],
                y=[0, loadings[i, 1] * scaling_factor],
                z=[0, loadings[i, 2] * scaling_factor],
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
            xaxis_title=f"PC1 ({pca.explained_variance_ratio_[0]:.1%} explained var)",
            yaxis_title=f"PC2 ({pca.explained_variance_ratio_[1]:.1%} explained var)",
            zaxis_title=f"PC3 ({pca.explained_variance_ratio_[2]:.1%} explained var)",
            aspectmode="cube",
        ),
        width=600,
        height=600,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.01,  # Position at bottom
            xanchor="center",  # Center anchor
            x=0.5,  # Center position
            orientation="h",  # Make legend horizontal
        ),
        margin=dict(l=0, r=0, t=30, b=50),  # Increased bottom margin for legend
    )

    # Add view buttons using updatemenus
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        args=[
                            {
                                "scene.camera": dict(
                                    eye=dict(x=1.5, y=1.5, z=1.5),
                                    center=dict(x=0, y=0, z=0),
                                )
                            }
                        ],
                        label="Reset View",
                        method="relayout",
                    ),
                    dict(
                        args=[
                            {
                                "scene.camera": dict(
                                    eye=dict(x=0, y=0, z=2), center=dict(x=0, y=0, z=0)
                                )
                            }
                        ],
                        label="XY View",
                        method="relayout",
                    ),
                    dict(
                        args=[
                            {
                                "scene.camera": dict(
                                    eye=dict(x=0, y=2, z=0), center=dict(x=0, y=0, z=0)
                                )
                            }
                        ],
                        label="XZ View",
                        method="relayout",
                    ),
                    dict(
                        args=[
                            {
                                "scene.camera": dict(
                                    eye=dict(x=2, y=0, z=0), center=dict(x=0, y=0, z=0)
                                )
                            }
                        ],
                        label="YZ View",
                        method="relayout",
                    ),
                ],
                direction="down",  # Stack buttons vertically
                pad={"r": 10, "t": 10},
                x=0.98,  # Position on right side
                y=0.9,  # Position near top
                xanchor="right",
                yanchor="top",
            )
        ]
    )

    # Add legend for PC colors (without Observations)
    for i, (pc, color) in enumerate(
        [("PC1", colors[0]), ("PC2", colors[1]), ("PC3", colors[2])]
    ):
        fig.add_trace(
            go.Scatter3d(
                x=[None],
                y=[None],
                z=[None],
                mode="markers",
                marker=dict(size=10, color=color),
                name=f"Dominant {pc}",
                showlegend=True,
            )
        )

    st.plotly_chart(fig, use_container_width=True)
