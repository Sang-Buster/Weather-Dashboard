import pandas as pd
import streamlit as st
from pymongo import MongoClient
import time


@st.cache_resource
def init_connection():
    """Initialize MongoDB connection optimized for large datasets"""
    return MongoClient(
        st.secrets["mongo"]["uri"],
        maxPoolSize=100,  # Increased for parallel operations
        minPoolSize=20,  # More ready connections
        maxIdleTimeMS=45000,  # Longer idle timeout for connection reuse
        connectTimeoutMS=5000,  # Quick connection timeout
        socketTimeoutMS=45000,  # Longer socket timeout for large data transfers
        serverSelectionTimeoutMS=5000,  # Quick server selection
        retryWrites=True,
        retryReads=True,
        compressors=["zstd"],  # Best compression/speed ratio
        maxConnecting=8,  # More parallel connections
        w="majority",  # Ensure consistency
        readPreference="secondaryPreferred",  # Read from secondaries when possible
    )


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


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_data_cached(min_date, max_date):
    """Cached version of data loading from MongoDB"""
    try:
        client = init_connection()
        db = client["weather_dashboard"]
        collection = db["weather_data"]

        # Query all documents at once (cached version)
        cursor = collection.find(
            {
                "tNow": {
                    "$gte": min_date,
                    "$lte": max_date,
                }
            },
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
                "SonicTemp_C": 1,
            },
        )

        documents = list(cursor)
        return documents
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return []


def load_data():
    """Load weather data with progress updates and caching"""
    try:
        if "date_range" not in st.session_state:
            date_range = get_date_range()
            if date_range is None:
                return pd.DataFrame()
            st.session_state["date_range"] = date_range

        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Get cached documents
        documents = fetch_data_cached(
            st.session_state.date_range["min_date"],
            st.session_state.date_range["max_date"],
        )

        # Process documents with progress updates
        total_count = len(documents)
        df_list = []

        for i, doc in enumerate(documents):
            df_list.append(doc)
            if i % 1000 == 0:  # Update progress every 1000 records
                progress = min(i / total_count, 1.0)
                progress_bar.progress(progress)
                status_text.text(f"Processing data... {i:,} of {total_count:,} records")

        # Convert to DataFrame
        df = pd.DataFrame(df_list)

        if len(df) > 0:
            # Convert and sort by timestamp
            df["tNow"] = pd.to_datetime(df["tNow"], utc=True)
            df.sort_values("tNow", inplace=True)

            # Add derived columns
            df["hour"] = df["tNow"].dt.hour
            df["day"] = df["tNow"].dt.day

        # Clear progress indicators after a short delay
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()

        if len(df) == 0:
            st.toast("No data found in the database", icon="❌")
        else:
            st.toast(f"Loaded {len(df):,} records successfully", icon="✅")

        # Store in session state
        st.session_state.full_df = df
        return df

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()


def filter_data(df, start_date, end_date):
    """Optimized dataframe filtering"""
    # Convert dates once
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)

    # Use vectorized operations with pre-computed dates
    mask = (df["tNow"].dt.date >= start_ts.date()) & (
        df["tNow"].dt.date <= end_ts.date()
    )
    filtered_df = df.loc[mask]

    return filtered_df
