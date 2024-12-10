from web_components import (
    wind_rose_component,
    wind_time_series_component,
    environmental_time_series_component,
    time_selection_component,
    # correlation_plot_component,
    scatter_plot_component,
    # pca_explained_variance_component,
    # pca_biplot_components,
    # roc_curve_plot_component,
    # pr_curve_plot_component,
    # predicted_plot_components,
    wind_3d_component,
)

import sys
from pathlib import Path
import streamlit as st


# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

    #####################
    # EDA section title #
    #####################
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
        # correlation_plot_component()
        wind_3d_component()
    with col4:
        scatter_plot_component()

    # # Explained Variance Plot + PCA Biplot
    # col5, col6 = st.columns(2)
    # with col5:
    #     pca_explained_variance_component()
    # with col6:
    #     pca_biplot_components()

    ####################
    # ML section title #
    ####################
    # st.markdown(
    #     "<hr><br><h2 style='text-align: center;'>🤖 Machine Learning Insights 🤖</h2>",
    #     unsafe_allow_html=True,
    # )

    # # ROC + PR curves
    # col7, col8 = st.columns(2)
    # with col7:
    #     roc_curve_plot_component()
    # with col8:
    #     pr_curve_plot_component()

    # # Predictions Plot
    # predicted_plot_components()


if __name__ == "__main__":
    main()
