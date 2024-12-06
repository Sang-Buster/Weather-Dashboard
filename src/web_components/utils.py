import pandas as pd
import streamlit as st
from pymongo import MongoClient


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
    """Load weather data using chunked aggregation for large datasets"""
    try:
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

        # Get total count first
        count_pipeline = [
            {
                "$match": {
                    "tNow": {
                        "$gte": st.session_state.date_range["min_date"],
                        "$lte": st.session_state.date_range["max_date"],
                    }
                }
            },
            {"$count": "total"},
        ]
        total_count = list(collection.aggregate(count_pipeline))[0]["total"]

        # Initialize empty DataFrame
        chunks = []
        chunk_size = 50000  # Process 50k documents at a time
        processed = 0

        # Chunked aggregation pipeline
        while processed < total_count:
            pipeline = [
                # Use index for date range
                {
                    "$match": {
                        "tNow": {
                            "$gte": st.session_state.date_range["min_date"],
                            "$lte": st.session_state.date_range["max_date"],
                        }
                    }
                },
                # Project all fields
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
                # Sort by date
                {"$sort": {"tNow": 1}},
                # Skip processed documents
                {"$skip": processed},
                # Limit chunk size
                {"$limit": chunk_size},
            ]

            # Process chunk
            cursor = collection.aggregate(
                pipeline,
                allowDiskUse=True,
                batchSize=10000,
            )

            # Convert chunk to DataFrame
            chunk_df = pd.DataFrame(list(cursor))
            if not chunk_df.empty:
                chunks.append(chunk_df)

            # Update progress
            processed += len(chunk_df)
            progress = min(processed / total_count, 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Loaded {processed:,} of {total_count:,} records...")

        # Combine all chunks
        if chunks:
            df = pd.concat(chunks, ignore_index=True)

            # Optimize datetime operations
            df["tNow"] = pd.to_datetime(df["tNow"], utc=True)
            # Vectorized operations
            df["hour"] = df["tNow"].dt.hour
            df["day"] = df["tNow"].dt.day

            # Final progress update
            progress_bar.progress(1.0)
            status_text.text(f"Loaded {len(df):,} records successfully")
        else:
            df = pd.DataFrame()
            st.error("No data found in the database")

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
