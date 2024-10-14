import streamlit as st
from components.utils import load_data, filter_data
from datetime import timedelta


def time_selection_component():
    # Load the data
    df = load_data()

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

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            "Location: 60ft up on a light pole @ [here](https://maps.app.goo.gl/noC7dszEV9brfdxy8)"
        )

    with col2:
        if not df.empty:
            first_update = df["tNow"].min().strftime("%m/%d/%Y %H:%M:%S")
            last_update = df["tNow"].max().strftime("%m/%d/%Y %H:%M:%S")
            st.markdown(f"Data Range: [{first_update}] - [{last_update}]")
        else:
            st.markdown("Data Range: N/A")

    # Unpack the selected dates
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        st.error("Please select both start and end dates.")
        return

    # Ensure start_date is not after end_date
    if start_date > end_date:
        st.error("Error: Start date must be before or equal to end date.")
        return

    # Filter data based on selected date range
    filtered_df = filter_data(df, start_date, end_date)

    if filtered_df.empty:
        st.error("No data available for the selected date range.")
    else:
        st.session_state.filtered_df = filtered_df
