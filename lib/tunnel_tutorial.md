# Tunneling a Local Streamlit App Using zrok

## **1. Install zrok**
Download and install `zrok` by following the official installation guide in the [zrok documentation](https://docs.zrok.io/docs/getting-started/).

## **2. Authenticate with zrok**
After signing up for a `zrok` account and verifying your email, you need to enable `zrok` using your account token. Run:

```bash
zrok enable <your_account_token>
```

This command links your machine to your `zrok` account.

## **3. Reserve a Public Share**
To create a reserved public share with a unique name (`erauweather`) and proxy backend pointing to port **8501**, run:

```bash
zrok reserve public --unique-name erauweather --backend-mode proxy 8501
```

This will generate a **public endpoint** at https://erauweather.sahre.zrok.io

## **4. Start the Reserved zrok Share in a Detached Screen Session**
To ensure the tunnel runs in the background, start the `zrok share` process in a detached `screen` session named `weather_app_cloud`:

```bash
screen -dmS weather_app_cloud zrok share reserved erauweather
```

---

## **Shell Scripts**

### **Script to Run Streamlit App in Screen (`start_weather_app_local.sh`)**
This script handles killing any existing process on port 8501, activates the virtual environment, and starts the Streamlit app in a screen session:

```bash
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
```

### **Script to Start zrok Tunnel in Screen (`start_weather_app_cloud.sh`)**
This script handles starting the zrok tunnel in a detached screen session:

```bash
#!/bin/bash

# Kill existing screen session if it exists
screen -X -S weather_app_cloud quit 2>/dev/null || true

# Start the zrok tunnel in a detached screen session
screen -dmS weather_app_cloud zrok share reserved erauweather
echo "zrok tunnel started in screen session: weather_app_cloud"
```

---

### **How to Use**
1. **Run the Streamlit app**:
   ```bash
   bash start_weather_app_local.sh
   ```
2. **Run the zrok tunnel**:
   ```bash
   bash start_weather_app_cloud.sh
   ```
3. **Check running screen sessions**:
   ```bash
   screen -ls
   ```
4. **Attach to a session (e.g., weather_app_cloud)**:
   ```bash
   screen -r weather_app_cloud
   ```
5. **Detach from a session (inside screen)**:
   Press `Ctrl+A`, then `D`.

---

### **Stopping the Processes**
To stop both the Streamlit app and the zrok tunnel:
```bash
screen -X -S weather_app_local quit
screen -X -S weather_app_cloud quit
```

---

Now your local Streamlit app is **accessible via**:

```
https://erauweather.sahre.zrok.io
```

🚀 Enjoy your **publicly accessible** Streamlit weather dashboard with `zrok`!