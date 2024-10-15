import pandas as pd
import streamlit as st
from pymongo import MongoClient


@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["mongo"]["uri"])


@st.cache_data(show_spinner="Loading data...")
def load_data():
    client = init_connection()
    db = client["weather_dashboard"]
    collection = db["weather_data"]
    data = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)
    df["tNow"] = pd.to_datetime(df["tNow"])
    return df


def filter_data(df, start_date, end_date):
    return df[(df["tNow"].dt.date >= start_date) & (df["tNow"].dt.date <= end_date)]
