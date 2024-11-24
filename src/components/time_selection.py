import streamlit as st
from components.utils import load_data, filter_data
from datetime import timedelta


def time_selection_component():
    # Load the data and store in session state
    df = load_data()

    if df.empty:
        st.error("""The database is empty. Please upload some data in the following format to get started.

    df = pd.DataFrame(columns=["tNow", "u_m_s", "v_m_s", "w_m_s", "2dSpeed_m_s", "3DSpeed_m_s", "Azimuth_deg", "Elev_deg", "Press_Pa", "Temp_C", "Hum_RH", "SonicTemp_C", "Error"])""")
        return st.stop()

    # Get the date range from the data
    min_date = df["tNow"].min().date()
    max_date = df["tNow"].max().date()

    # Set default date range
    default_end_date = max_date
    default_start_date = max(min_date, (df["tNow"].max() - timedelta(days=1)).date())

    # Date range picker
    selected_dates = st.date_input(
        "Select date range",
        (default_start_date, default_end_date),
        min_value=min_date,
        max_value=max_date,
        format="MM/DD/YYYY",
    )

    # Display metadata
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(
            "**Location**: 60ft up on a light pole @ [here](https://maps.app.goo.gl/noC7dszEV9brfdxy8)"
        )
    with col2:
        first_update = df["tNow"].min().strftime("%m/%d/%Y %H:%M:%S")
        last_update = df["tNow"].max().strftime("%m/%d/%Y %H:%M:%S")
        st.markdown(f"**Data Range**: {first_update} - {last_update}")

    # Handle date selection
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        st.error("Please select both start and end dates.")
        return

    if start_date > end_date:
        st.error("Error: Start date must be before or equal to end date.")
        return

    # Filter data and store in session state
    filtered_df = filter_data(df, start_date, end_date)

    if filtered_df.empty:
        st.error("No data available for the selected date range.")
