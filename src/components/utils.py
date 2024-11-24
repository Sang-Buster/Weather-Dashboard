import pandas as pd
import streamlit as st
from pymongo import MongoClient


@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["mongo"]["uri"])


@st.cache_data(ttl=3600)
def get_analysis_data(collection_name, data_type):
    """Get analysis data from MongoDB collection by type."""
    try:
        client = MongoClient(st.secrets["mongo"]["uri"])
        db = client["weather_dashboard"]
        collection = db[collection_name]

        # Debug: Print all documents in collection
        print(f"\nDebug: Checking {collection_name} for {data_type}")
        all_docs = list(collection.find({}, {"_id": 0}))
        print(f"Found {len(all_docs)} documents:")
        for doc in all_docs:
            print(f"Document: {doc.get('type', 'no_type')}")
            if "data" in doc:
                print(f"Keys in data: {list(doc['data'].keys())}")

        # Query for document with specific type
        document = collection.find_one({"type": data_type})

        if document:
            print(f"Found document with type {data_type}")
            if "data" in document:
                return document["data"]
            print("Warning: Document has no 'data' field")
            return document  # Return the whole document if no data field

        print(f"No document found with type {data_type}")
        return None

    except Exception as e:
        print(f"MongoDB Error: {str(e)}")
        st.error(f"Error connecting to MongoDB: {e}")
        return None


@st.cache_data(ttl=3600)
def load_data():
    """Load weather data from MongoDB efficiently"""
    try:
        client = init_connection()
        db = client["weather_dashboard"]
        collection = db["weather_data"]

        # Get min and max dates first (faster than sorting everything)
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "min_date": {"$min": "$tNow"},
                    "max_date": {"$max": "$tNow"},
                }
            }
        ]
        date_range = list(collection.aggregate(pipeline))[0]
        
        # Fetch only necessary fields
        projection = {
            "_id": 0,
            "metadata": 0,
            "Error": 0,  # Exclude if not needed
            "SonicTemp_C": 0  # Exclude if not needed
        }

        # Fetch documents with minimal processing
        cursor = collection.find(
            {},
            projection
        ).hint([("tNow", 1)])  # Use the existing index

        # Convert to DataFrame efficiently
        df = pd.DataFrame(list(cursor))
        
        if df.empty:
            return pd.DataFrame()

        # Convert to datetime once at the end
        df["tNow"] = pd.to_datetime(df["tNow"])
        
        # Sort in pandas (usually faster than MongoDB for this case)
        df.sort_values("tNow", inplace=True)
        
        # Store in session state
        st.session_state.full_df = df
        st.session_state.date_range = {
            "min_date": pd.to_datetime(date_range["min_date"]),
            "max_date": pd.to_datetime(date_range["max_date"])
        }
        
        return df

    except Exception as e:
        st.error(f"Error loading weather data from MongoDB: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_date_range():
    """Get min and max dates from the data"""
    if "date_range" in st.session_state:
        return st.session_state.date_range
    return None


def filter_data(df, start_date, end_date):
    """Filter dataframe by date range and store in session state"""
    filtered_df = df[
        (df["tNow"].dt.date >= start_date) & (df["tNow"].dt.date <= end_date)
    ]

    # Store filtered data in session state
    st.session_state.filtered_df = filtered_df
    return filtered_df
