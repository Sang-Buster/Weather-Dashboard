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

This will generate a **public endpoint** at https://erauweather.share.zrok.io/

## **4. Start the Reserved zrok Share in a Detached Screen Session**
Two shell scripts are provided to manage the Streamlit app and zrok tunnel:

- `start_weather_app_local.sh`: Starts the Streamlit app in a screen session
- `start_weather_app_cloud.sh`: Starts the zrok tunnel in a screen session

Both scripts handle cleaning up existing processes and creating new screen sessions automatically.

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

Now your local Streamlit app is **accessible via**: https://erauweather.share.zrok.io/