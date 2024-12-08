import streamlit as st
import plotly.graph_objects as go
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from web_components.utils import get_analysis_data


def pca_biplot_components():
    try:
        # Load PCA data from MongoDB
        pca_data = get_analysis_data("pca_results", "pca_data")
        if not pca_data:
            st.error("PCA data not found in database. Please run the analysis first.")
            return

        # Check if filtered_df exists in session state
        if "filtered_df" not in st.session_state:
            st.error("No data loaded. Please upload data first.")
            return

        biplot_data = pca_data["biplot_data"]
        features = biplot_data["features"]

        # Check if all required features are present in the dataframe
        missing_features = [
            f for f in features if f not in st.session_state.filtered_df.columns
        ]
        if missing_features:
            st.error(f"Missing required features: {missing_features}")
            return

        pc_coordinates = np.array(biplot_data["pc_coordinates"])
        explained_variance_3d = biplot_data["explained_variance_3d"]

        # Create the 3D scatter plot
        fig = go.Figure()

        # Get PC scores from the data
        df = st.session_state.filtered_df

        # Handle missing values
        df_clean = df[features].copy()

        # Option 1: Drop rows with any missing values
        df_clean = df_clean.dropna()

        # Option 2: Or impute missing values with mean (uncomment if you prefer this approach)
        # df_clean = df_clean.fillna(df_clean.mean())

        if len(df_clean) == 0:
            st.error("No valid data points after removing missing values.")
            return

        # Standardize the features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(df_clean)

        # Perform PCA to get scores
        pca = PCA()
        pc_scores = pca.fit_transform(scaled_features)

        # Determine dominant PC for each point
        pc_abs = np.abs(pc_scores[:, :3])
        dominant_pc = np.argmax(pc_abs, axis=1)
        colors = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
        ]  # Blue, Orange, Green for PC1, PC2, PC3
        point_colors = [colors[pc] for pc in dominant_pc]

        # Add scatter points with color based on dominant PC
        fig.add_trace(
            go.Scatter3d(
                x=pc_scores[:, 0],
                y=pc_scores[:, 1],
                z=pc_scores[:, 2],
                mode="markers",
                marker=dict(size=4, opacity=0.6, color=point_colors),
                hovertemplate=(
                    "PC1: %{x:.2f}<br>"
                    + "PC2: %{y:.2f}<br>"
                    + "PC3: %{z:.2f}<extra></extra>"
                ),
                showlegend=False,
            )
        )

        # Add loading vectors
        scaling_factor = 3
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
                    hoverinfo="none",
                )
            )

        # Update layout
        fig.update_layout(
            scene=dict(
                xaxis_title=f"PC1 ({explained_variance_3d[0]:.1f}%)",
                yaxis_title=f"PC2 ({explained_variance_3d[1]:.1f}%)",
                zaxis_title=f"PC3 ({explained_variance_3d[2]:.1f}%)",
            ),
            margin=dict(l=0, r=0, b=0, t=0),
        )

        # Display the plot
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading PCA biplot: {str(e)}")
