import streamlit as st
from components.wind_rose import wind_rose_component
from components.wind_time_series import wind_time_series_component
from components.env_time_series import environmental_time_series_component
from components.time_selection import time_selection_component

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

    time_selection_component()

    # Create a 2x2 grid layout
    col1, col2 = st.columns(2)

    with col1:
        wind_rose_component()

    with col2:
        environmental_time_series_component()

    wind_time_series_component()


if __name__ == "__main__":
    main()
