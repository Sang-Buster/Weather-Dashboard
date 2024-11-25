import pandas as pd
import streamlit as st
from pymongo import MongoClient


@st.cache_resource
def init_connection():
    return MongoClient(
        st.secrets["mongo"]["uri"],
        maxPoolSize=10,
        minPoolSize=5,
    )


@st.cache_data(ttl=3600)
def get_analysis_data(collection_name, data_type):
    """Get analysis data from MongoDB collection by type."""
    try:
        client = init_connection()
        db = client["weather_dashboard"]
        collection = db[collection_name]

        document = collection.find_one({"type": data_type}, {"_id": 0, "data": 1})

        if document and "data" in document:
            return document["data"]
        return document if document else None

    except Exception as e:
        st.error(f"Error connecting to MongoDB: {e}")
        return None


def get_date_range():
    """Get date range from MongoDB without loading all data"""
    try:
        client = init_connection()
        db = client["weather_dashboard"]
        collection = db["weather_data"]

        # Get min and max dates using aggregation
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "min_date": {"$min": "$tNow"},
                    "max_date": {"$max": "$tNow"},
                }
            }
        ]

        result = list(collection.aggregate(pipeline))

        if not result:
            return None

        date_range = {
            "min_date": pd.to_datetime(result[0]["min_date"]),
            "max_date": pd.to_datetime(result[0]["max_date"]),
        }

        # Store in session state
        st.session_state["date_range"] = date_range
        return date_range

    except Exception as e:
        st.error(f"Error getting date range: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def load_data():
    """Load weather data from MongoDB efficiently"""
    try:
        # First ensure we have date range
        if "date_range" not in st.session_state:
            date_range = get_date_range()
            if date_range is None:
                return pd.DataFrame()

        client = init_connection()
        db = client["weather_dashboard"]
        collection = db["weather_data"]

        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Get total count
        total_count = collection.count_documents({})

        if total_count == 0:
            st.error("No data found in the database")
            return pd.DataFrame()

        # Use aggregation pipeline for efficient processing
        pipeline = [
            {
                "$project": {
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
                    "SonicTemp_C": 1,
                }
            },
            {"$sort": {"tNow": 1}},
        ]

        # Process data in batches
        all_data = []
        documents_processed = 0

        cursor = collection.aggregate(
            pipeline,
            allowDiskUse=True,
            batchSize=5000,  # Adjusted batch size
        )

        for doc in cursor:
            all_data.append(doc)
            documents_processed += 1

            if documents_processed % 1000 == 0:
                progress = documents_processed / total_count
                progress_bar.progress(progress)
                status_text.text(
                    f"Loading data... {documents_processed:,} of {total_count:,} records"
                )

        # Create DataFrame
        df = pd.DataFrame(all_data)

        if df.empty:
            return pd.DataFrame()

        # Process DataFrame
        df["tNow"] = pd.to_datetime(df["tNow"])
        df["hour"] = df["tNow"].dt.hour
        df["day"] = df["tNow"].dt.day

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        # Store in session state
        st.session_state.full_df = df
        return df

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()


def filter_data(df, start_date, end_date):
    """Filter dataframe by date range and store in session state"""
    filtered_df = df[
        (df["tNow"].dt.date >= start_date) & (df["tNow"].dt.date <= end_date)
    ]

    # Store filtered data in session state
    st.session_state.filtered_df = filtered_df
    return filtered_df
