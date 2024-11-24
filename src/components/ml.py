import streamlit as st
import plotly.graph_objects as go
from components.utils import get_analysis_data
import pandas as pd


def load_plot_data():
    """Load saved plot data from MongoDB"""
    plot_data = get_analysis_data("ml_results", "ml_plot_data")
    if not plot_data:
        raise FileNotFoundError("ML plot data not found in database")
    return plot_data


def roc_curve_plot_component():
    """ROC Curve Component"""
    # Load saved data
    plot_data = load_plot_data()

    # Create ROC curve plot
    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for name, color in zip(["LR", "DT", "RF"], colors):
        data = plot_data[f"{name}_ROC"]
        fig.add_trace(
            go.Scatter(
                x=data["fpr"],
                y=data["tpr"],
                name=f"{name} (AUC = {data['auc_score']:.3f})",
                line=dict(color=color),
                mode="lines",
            )
        )

    # Add diagonal line
    fig.add_trace(
        go.Scatter(
            x=[0, 1], y=[0, 1], line=dict(color="gray", dash="dash"), showlegend=False
        )
    )

    fig.update_layout(
        title={"text": "ROC Curves", "x": 0.5, "xanchor": "center", "yanchor": "top"},
        xaxis_title="False Positive Rate",
        yaxis_title="True Positive Rate",
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(yanchor="top", y=0.01, xanchor="center", x=0.5, orientation="h"),
    )

    st.plotly_chart(fig, use_container_width=True)


def pr_curve_plot_component():
    """PR Curve Component"""
    # Load saved data
    plot_data = load_plot_data()

    # Create PR curve plot
    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for name, color in zip(["LR", "DT", "RF"], colors):
        data = plot_data[f"{name}_PR"]
        fig.add_trace(
            go.Scatter(
                x=data["recall"],
                y=data["precision"],
                name=f"{name} (AP = {data['ap_score']:.3f})",
                line=dict(color=color),
                mode="lines",
            )
        )

    fig.update_layout(
        title={
            "text": "Precision-Recall Curves",
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        xaxis_title="Recall",
        yaxis_title="Precision",
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(yanchor="top", y=0.01, xanchor="center", x=0.5, orientation="h"),
    )

    st.plotly_chart(fig, use_container_width=True)


def predicted_plot_components():
    """Predictions Plot Component"""
    try:
        # Load prediction data from MongoDB
        pred_data = get_analysis_data("ml_results", "ml_prediction_data")
        if not pred_data:
            st.error("Prediction data not found in database")
            return

        # Add loading indicator
        with st.spinner("Generating prediction plot..."):
            fig = go.Figure()

            # Convert time indices to datetime once and store
            time_index = pd.to_datetime(pred_data["time_index"])

            # Downsample actual wind speed data for faster plotting
            downsample_factor = max(
                len(pred_data["actual_speed"]) // 5000, 1
            )  # Limit to 5000 points
            fig.add_trace(
                go.Scatter(
                    x=time_index[::downsample_factor],
                    y=pred_data["actual_speed"][::downsample_factor],
                    name="Actual Wind Speed",
                    line=dict(color="gray", width=1),
                    mode="lines",
                    hovertemplate="Time: %{x}<br>Speed: %{y:.2f} m/s<extra></extra>",
                )
            )

            # Add threshold line (this is lightweight)
            fig.add_hline(
                y=pred_data["threshold"],
                line_dash="dash",
                line_color="red",
                annotation_text=f"Threshold ({pred_data['threshold']} m/s)",
                annotation_position="right",
            )

            # Add model predictions (these are already sparse)
            colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
            for name, color in zip(["LR", "DT", "RF"], colors):
                data = pred_data[f"{name}_predictions"]
                if data["indices"]:
                    fig.add_trace(
                        go.Scatter(
                            x=[time_index[i] for i in data["indices"]],
                            y=data["speeds"],
                            mode="markers",
                            name=f"{name} Predictions",
                            marker=dict(color=color, size=8, opacity=0.6),
                            hovertemplate=f"{name}<br>Time: %{{x}}<br>Speed: %{{y:.2f}} m/s<extra></extra>",
                        )
                    )

            # Optimize layout for performance
            fig.update_layout(
                title={
                    "text": "Wind Speed Predictions",
                    "x": 0.5,
                    "xanchor": "center",
                    "yanchor": "top",
                },
                xaxis_title="Time",
                yaxis_title="Wind Speed (m/s)",
                height=800,
                showlegend=True,
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                margin=dict(l=0, r=0, t=30, b=0),
                hovermode="closest",  # Faster than default hover mode
                # Simplify grid for better performance
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="rgba(128, 128, 128, 0.2)",
                    rangeslider=dict(visible=True, thickness=0.05),
                ),
                yaxis=dict(
                    showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)"
                ),
            )

            # Use streamlit's plotting with optimized config
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "scrollZoom": True,
                    "displayModeBar": True,
                    "displaylogo": False,
                    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                    "staticPlot": False,  # Set to True for even faster rendering if interactivity isn't needed
                    "responsive": True,
                },
            )

    except Exception as e:
        st.error(f"Error loading prediction data: {str(e)}")
