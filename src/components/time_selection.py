import streamlit as st
from components.utils import load_data, filter_data, get_date_range
from datetime import timedelta


def time_selection_component():
    # Always try to load data and date range if not in session state
    if "full_df" not in st.session_state:
        df = load_data()
        if df.empty:
            st.error("Failed to load data. Please check the database connection.")
            return st.stop()
        st.session_state.full_df = df

    if "date_range" not in st.session_state:
        date_range = get_date_range()
        if date_range is None:
            st.error("Failed to get date range from database.")
            return st.stop()
        st.session_state.date_range = date_range

    # Now we can safely use date_range
    min_date = st.session_state.date_range["min_date"].date()
    max_date = st.session_state.date_range["max_date"].date()

    # Set default date range to last 24 hours
    default_end_date = max_date
    default_start_date = (
        st.session_state.date_range["max_date"] - timedelta(hours=24)
    ).date()

    # Date range picker with try-except block
    try:
        selected_dates = st.date_input(
            "Select date range",
            (default_start_date, default_end_date),
            min_value=min_date,
            max_value=max_date,
            format="MM/DD/YYYY",
        )

        # Handle incomplete date selection
        if not isinstance(selected_dates, tuple) or len(selected_dates) != 2:
            st.warning("Please select both start and end dates.")
            return st.stop()

        start_date, end_date = selected_dates

        if start_date > end_date:
            st.error("Error: Start date must be before or equal to end date.")
            return st.stop()

        # Always filter data when dates are selected
        filtered_df = filter_data(st.session_state.full_df, start_date, end_date)
        if filtered_df.empty:
            st.error("No data available for the selected date range.")
            return st.stop()

        # Store filtered DataFrame in session state
        st.session_state.filtered_df = filtered_df

    except Exception as e:
        st.error(f"Error with date selection: {str(e)}")
        return st.stop()

    # Display metadata
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(
            "**Location**: 60ft up on a light pole @ [here](https://maps.app.goo.gl/noC7dszEV9brfdxy8)"
        )
    with col2:
        first_update = st.session_state.date_range["min_date"].strftime(
            "%m/%d/%Y %H:%M:%S"
        )
        last_update = st.session_state.date_range["max_date"].strftime(
            "%m/%d/%Y %H:%M:%S"
        )
        st.markdown(f"**Data Range**: {first_update} - {last_update}")
