import pandas as pd
import streamlit as st


@st.cache_data
def load_data():
    return pd.read_csv(
        "src/data/current_weather_data_logfile.csv", parse_dates=["tNow"]
    )


def filter_data(df, start_date, end_date):
    return df[(df["tNow"].dt.date >= start_date) & (df["tNow"].dt.date <= end_date)]
