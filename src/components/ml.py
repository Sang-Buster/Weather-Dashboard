import streamlit as st
import plotly.graph_objects as go
import json


def load_plot_data():
    """Load saved plot data"""
    with open("src/data/ml_plot_data.json", "r") as f:
        return json.load(f)


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
    # Load prediction data
    with open("src/data/ml_prediction_data.json", "r") as f:
        pred_data = json.load(f)

    fig = go.Figure()

    # Add actual wind speed
    fig.add_trace(
        go.Scatter(
            x=pred_data["time_index"],
            y=pred_data["actual_speed"],
            name="Actual Wind Speed",
            line=dict(color="gray", width=1),
            mode="lines",
        )
    )

    # Add threshold line
    fig.add_hline(
        y=pred_data["threshold"],
        line_dash="dash",
        line_color="red",
        annotation_text=f"Threshold ({pred_data['threshold']} m/s)",
        annotation_position="right",
    )

    # Add model predictions
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    for name, color in zip(["LR", "DT", "RF"], colors):
        data = pred_data[f"{name}_predictions"]
        if data["indices"]:
            fig.add_trace(
                go.Scatter(
                    x=[pred_data["time_index"][i] for i in data["indices"]],
                    y=data["speeds"],
                    mode="markers",
                    name=f"{name} Predictions",
                    marker=dict(color=color, size=8, opacity=0.6),
                )
            )

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
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")

    st.plotly_chart(fig, use_container_width=True)
