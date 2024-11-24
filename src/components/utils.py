import pandas as pd
import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta


@st.cache_resource
def init_connection():
    return MongoClient(
        st.secrets["mongo"]["uri"],
        maxPoolSize=10,
        minPoolSize=5,
        maxIdleTimeMS=45000,
        waitQueueTimeoutMS=5000 
    )


@st.cache_data(ttl=3600)
def get_analysis_data(collection_name, data_type):
    """Get analysis data from MongoDB collection by type."""
    try:
        client = init_connection()
        db = client["weather_dashboard"]
        collection = db[collection_name]

        document = collection.find_one(
            {"type": data_type},
            {"_id": 0, "data": 1}
        )

        if document and "data" in document:
            return document["data"]
        return document if document else None

    except Exception as e:
        st.error(f"Error connecting to MongoDB: {e}")
        return None


@st.cache_data(ttl=3600)
def load_data():
    """Load weather data from MongoDB efficiently"""
    try:
        client = init_connection()
        db = client["weather_dashboard"]
        collection = db["weather_data"]

        # First get the date range using aggregation
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "min_date": {"$min": "$tNow"},
                    "max_date": {"$max": "$tNow"}
                }
            }
        ]
        date_range = list(collection.aggregate(pipeline))
        
        if not date_range:
            st.error("No data found in the database")
            return pd.DataFrame()
        
        # Convert strings to datetime objects before storing
        min_date = pd.to_datetime(date_range[0]["min_date"])
        max_date = pd.to_datetime(date_range[0]["max_date"])
        
        # Store in session state without caching
        if "date_range" not in st.session_state:
            st.session_state["date_range"] = {
                "min_date": min_date,
                "max_date": max_date
            }
        
        # Rest of your existing load_data code...
        data = list(collection.find(
            {},
            {
                "_id": 0,
                "tNow": 1,
                "Temp_C": 1,
                "Press_Pa": 1,
                "Hum_RH": 1,
                "2dSpeed_m_s": 1,
                "3DSpeed_m_s": 1,
                "u_m_s": 1,
                "v_m_s": 1,
                "w_m_s": 1,
                "Azimuth_deg": 1,
                "Elev_deg": 1,
                "SonicTemp_C": 1
            }
        ).hint([("tNow", 1)]))
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return pd.DataFrame()

        df["tNow"] = pd.to_datetime(df["tNow"])
        df["hour"] = df["tNow"].dt.hour
        df["day"] = df["tNow"].dt.day
        
        st.session_state.full_df = df
        return df

    except Exception as e:
        st.error(f"Error loading weather data: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_date_range():
    """Get min and max dates from the data"""

    if "date_range" in st.session_state:
        date_range = st.session_state.date_range
        
        # Ensure we have datetime objects
        if isinstance(date_range, dict) and "min_date" in date_range and "max_date" in date_range:
            return {
                "min_date": pd.to_datetime(date_range["min_date"]),
                "max_date": pd.to_datetime(date_range["max_date"])
            }
    return None


def filter_data(df, start_date, end_date):
    """Filter dataframe by date range and store in session state"""
    filtered_df = df[
        (df["tNow"].dt.date >= start_date) & (df["tNow"].dt.date <= end_date)
    ]

    # Store filtered data in session state
    st.session_state.filtered_df = filtered_df
    return filtered_df
