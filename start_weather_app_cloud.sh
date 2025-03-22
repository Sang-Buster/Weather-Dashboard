#!/bin/bash

# Kill existing screen session if it exists
screen -X -S weather_app_cloud quit 2>/dev/null || true

# Start the zrok tunnel in a detached screen session
screen -dmS weather_app_cloud zrok share reserved erauweather
echo "zrok tunnel started in screen session: weather_app_cloud"
