#!/bin/bash

# Kill any process using port 8501
PID=$(lsof -ti :8501)
if [ -n "$PID" ]; then
    echo "Killing process on port 8501 (PID: $PID)"
    kill -9 $PID
    sleep 2
fi

# Change to the weather dashboard directory
cd /var/tmp/weather-dashboard || exit

# Activate virtual environment
source .venv/bin/activate

# Start the application inside a screen session
screen -dmS weather_app_local bash -c "streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0"
echo "Streamlit app started in screen session: weather_app_local"
