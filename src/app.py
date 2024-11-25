import os
import sys
import streamlit as st

from components.wind_rose import wind_rose_component
from components.wind_time_series import wind_time_series_component
from components.env_time_series import environmental_time_series_component
from components.time_selection import time_selection_component
from components.corre_plot import correlation_plot_component
from components.scatter_plot import scatter_plot_component
from components.explained_var_plot import pca_explained_variance_component
from components.pca_biplot import pca_biplot_components
from components.ml import (
    roc_curve_plot_component,
    pr_curve_plot_component,
    predicted_plot_components,
)


# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# App information
about_info = """
This dashboard provides an interactive visualization of weather data.

**Author:** 
- Sang Xing

**Contributors:** 
- Kaleb Nails
- Marc Compere
- Avinash Muthu Krishnan
"""


# Page configuration
st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    menu_items={
        "Report a bug": "https://github.com/Sang-Buster/weather-dashboard/issues/new",
        "About": about_info,
    },
)

# Initialize session state
if "filtered_df" not in st.session_state:
    st.session_state.filtered_df = None


def main():
    # Display the dashboard title
    st.markdown(
        "<h1 style='text-align: center;'>🌤️ Weather Dashboard 🌤️</h1>",
        unsafe_allow_html=True,
    )

    ###############
    # Date Picker #
    ###############
    time_selection_component()

    # #####################
    # # EDA section title #
    # #####################
    # Wind Rose Diagram + Env Conditions Plot
    col1, col2 = st.columns(2)
    with col1:
        wind_rose_component()
    with col2:
        environmental_time_series_component()

    # Wind Speed Time Series Plot
    wind_time_series_component()

    # Correlation Plot + Scatter Plot
    col3, col4 = st.columns(2)
    with col3:
        correlation_plot_component()
    with col4:
        scatter_plot_component()

    # Explained Variance Plot + PCA Biplot
    col5, col6 = st.columns(2)
    with col5:
        pca_explained_variance_component()
    with col6:
        pca_biplot_components()

    ####################
    # ML section title #
    ####################
    st.markdown(
        "<hr><br><h2 style='text-align: center;'>🤖 Machine Learning Insights 🤖</h2>",
        unsafe_allow_html=True,
    )

    # ROC + PR curves
    col7, col8 = st.columns(2)
    with col7:
        roc_curve_plot_component()
    with col8:
        pr_curve_plot_component()

    # Predictions Plot
    predicted_plot_components()


if __name__ == "__main__":
    main()
