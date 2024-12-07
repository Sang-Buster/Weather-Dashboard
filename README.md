<div align="center">
  <img src="lib/fig/logo.png" alt="Logo" width="15%">
  <h1 align="center">Weather Dashboard</h1>
</div>

This project is a comprehensive weather data analysis system that combines a [Streamlit web dashboard](#web-app-operations) for visualization, a [CLI tool (Meteorix)](#cli-operations) for data management, and a [Discord bot](#discord-bot-operations) for remote CLI operations. It focuses on analyzing [Hurricane Milton](https://en.wikipedia.org/wiki/Hurricane_Milton) wind patterns and provides interactive tools across multiple interfaces.


<div align='center'>
  <h2>Table of Contents</h2>
</div>

<ol>
  <li><a href="#web-app-operations">Web App Operations</a></li>
  <li><a href="#cli-operations">CLI Operations</a></li>
  <li><a href="#discord-bot-operations">Discord Bot Operations</a></li>
  <li><a href="#project-structure">Project Structure</a></li>
</ol>

<div align="center">
  <h2>Web App Operations</h2>
  <img src="lib/fig/dashboard.png" alt="Dashboard" width="100%">
</div>

### Setup Instructions

1. **Clone the repository and navigate to project folder:**
   ```bash
   git clone https://github.com/Sang-Buster/weather-dashboard
   cd weather-dashboard
   ```

2. **Install uv first:**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Create a virtual environment:**
   ```bash
   uv venv --python 3.12.1
   ```

4. **Activate the virtual environment:**
   ```bash
   # macOS/Linux
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

5. **Install the required packages:**
   ```bash
   uv pip install -r requirements.txt
   ```

6. **Create a `.streamlit/secrets.toml` file:**
   ```bash
   touch .streamlit/secrets.toml
   ```

7. **Add MongoDB URI to `secrets.toml`:**
   ```toml
   [mongo]
   uri = "mongodb+srv://<usr>:<pwd>@<xxxxxx.mongodb.net>/?retryWrites=true&w=majority&appName=Cluster0"
   ```

### Running the Web App
```bash
streamlit run src/app.py
```


<div align="center">
  <h2>CLI Operations</h2>
  <img src="lib/fig/banner.png" alt="Banner" width="60%">
</div>

### Setup Instructions

#### Option 1: Direct Python Command

Simply run the CLI tool directly with Python:
```bash
python src/cli.py --help
```

#### Option 2: Create CLI Alias (Optional)

For convenience, you can set up an alias named `meteorix`:

1. **Add Project Root to PYTHONPATH:**
   ```bash
   # Get your project root path
   cd /path/to/weather-dashboard
   export PYTHONPATH="$(pwd):$PYTHONPATH"
   ```

2. **Create CLI Alias:**
   ```bash
   # Create alias for the CLI tool
   alias meteorix="python src/cli.py"
   ```

3. **Make Changes Permanent:**
   Add these lines to your shell configuration file (`~/.bashrc` or `~/.zshrc`):
   ```bash
   REPO_DIR="/var/tmp/weather-dashboard"
   PYTHON_PATH="$REPO_DIR/.venv/bin/python"
   CLI_PATH="$REPO_DIR/src/cli.py"
   alias meteorix="$PYTHON_PATH $CLI_PATH"
   ```

4. **Apply Changes:**
   Either:
   - Restart your terminal, or
   - Run: `source ~/.bashrc` (or `source ~/.zshrc`)

5. **Show Available Commands:**
   ```bash
   meteorix --help
   ```

### Basic Usage
The following commands work with either method (replace `meteorix` with `python src/cli.py` if not using the alias):

```bash
# Show whoami
meteorix who

# Show available date range and file statistics
meteorix info

# Upload data for a specific date
meteorix upload 2024_03_20

# Show first/last 5 rows of data
meteorix head 2024_03_20
meteorix tail 2024_03_20
```


<div align="center">
  <h2>Discord Bot Operations</h2>
  <img src="lib/fig/bot.png" alt="Bot" width="40%">
</div>

### Setup Instructions

1. **Add Bot Token to `.streamlit/secrets.toml`:**
   ```toml
   [bot_token]
   token = "YOUR_BOT_TOKEN"

   [channel_id]
   channel_1_id = "YOUR_CHANNEL_ID_1"
   channel_2_id = "YOUR_CHANNEL_ID_2"
   # add more channels as needed
   ```

2. **Create Systemd Service File:**
   ```bash
   sudo nano /etc/systemd/system/meteorix-bot.service
   ```

3. **Add the following configuration** (adjust paths and username):
   ```ini
   [Unit]
   Description=Meteorix Discord Bot
   After=network.target

   [Service]
   Type=simple
   User=YOUR_USERNAME
   WorkingDirectory=/path/to/weather-dashboard
   Environment="PATH=/path/to/weather-dashboard/.venv/bin"
   ExecStart=/path/to/weather-dashboard/.venv/bin/python /path/to/weather-dashboard/src/meteorix.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. **Enable and Start the Service:**
   ```bash
   # Enable the service to start on boot
   sudo systemctl enable meteorix-bot

   # Start the service
   sudo systemctl start meteorix-bot

   # Check service status
   sudo systemctl status meteorix-bot
   ```

5. **Common Service Commands:**
   ```bash
   # Stop the bot
   sudo systemctl stop meteorix-bot

   # Restart the bot (after code changes)
   sudo systemctl restart meteorix-bot

   # View live logs
   sudo journalctl -u meteorix-bot -f
   ```

### Basic Usage

1. **Mention Commands:**
   ```
   @meteorix help          # Show all commands
   @meteorix info          # Show available date range
   @meteorix head          # Show earliest timestamp
   @meteorix tail          # Show latest timestamp
   ```

2. **Slash Commands:**
   ```
   /help                # Show all commands
   /info                # Show available date range
   /head 2024_03_20     # Show first 5 rows of specific date
   /tail                # Show latest timestamp
   ```


<div align='center'>
   <h2>Project Structure</h2>
</div>

```
📦weather-dashboard
 ┣ 📂.devcontainer               // Dev container configuration
 ┣ 📂.github                     // GitHub workflows and actions
 ┣ 📂.streamlit                  // Streamlit configuration files
 ┃ ┣ 📄config.toml                  // App configuration
 ┃ ┗ 📄secrets.toml                 // Secrets configuration
 ┣ 📂lib                         // Library and documentation files
 ┃ ┣ 📂fig                          // Plots and images
 ┃ ┣ 📄project_instructions.pdf
 ┃ ┣ 📄project_presentation.pdf
 ┃ ┣ 📄project_proposal.md
 ┃ ┗ 📄project_report.md
 ┣ 📂src                         // Source code files
 ┃ ┣ 📂cli_components               // CLI components
 ┃ ┣ 📂web_components               // Dashboard components
 ┃ ┣ 📂data                         // Data and analysis scripts
 ┃ ┣ 📄app.py                       // Web app main script
 ┃ ┣ 📄cli.py                       // CLI tool main script
 ┃ ┗ 📄meteorix.py                  // Discord bot script
 ┣ 📄.gitignore
 ┣ 📄LICENSE
 ┣ 📄README.md
 ┗ 📄requirements.txt            // Python dependencies
```
