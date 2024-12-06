<div align="center">
  <h1 align="center">Weather Dashboard</h1>
</div>

This project is a web application built with Streamlit that visualizes weather data, specifically focusing on wind data. It provides interactive controls and visualizations to help users understand [Hurricane Milton](https://en.wikipedia.org/wiki/Hurricane_Milton) behavior under various conditions.

<div align="center">
  <img src="lib/fig/banner.png" alt="Weather Dashboard Banner" width="100%">
</div>


## Setup Instructions

Follow these steps to set up the project environment after you have cloned this repo:

1. **Create a new [`conda`](https://github.com/conda-forge/miniforge) environment:**
   ```bash
   conda create -n tmp python=3.12 -y
   ```

2. **Activate the conda environment:**
   ```bash
   conda activate tmp
   ```

3. **Install [`uv`](https://docs.astral.sh/uv/) first:**
   ```bash
   pip install uv
   ```

4. **Install the required packages:**
   ```bash
   uv pip install -r requirements.txt
   ```

5. **Create a `.streamlit/secrets.toml` file and**
   ```bash
   touch .streamlit/secrets.toml
   ```

6. **Add the following content in `secrets.toml`, but use your own MongoDB URI:**
   ```toml
   [mongo]
   uri = "mongodb+srv://<usr>:<pwd>@<xxxxxx.mongodb.net>/?retryWrites=true&w=majority&appName=Cluster0"
   ```

7. **Run the Streamlit application:**
   ```bash
   streamlit run src/app.py
   ```

8. **Development Instructions-Code Linting:**
   ```bash
   ruff check src
   ruff format src
   ```

## CLI Operations

The project includes a CLI tool for managing weather data and analysis results. You can use it in two ways:

### Option 1: Direct Python Command

Simply run the CLI tool directly with Python:
```bash
python src/data/data_cli.py --help
```

### Option 2: Create CLI Alias (Optional)

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
   alias meteorix="python src/data/data_cli.py"
   ```

3. **Make Changes Permanent:**
   Add these lines to your shell configuration file (`~/.bashrc` or `~/.zshrc`):
   ```bash
   export PYTHONPATH="/absolute/path/to/weather-dashboard:$PYTHONPATH"
   alias meteorix="python src/data/data_cli.py"
   ```

4. **Apply Changes:**
   Either:
   - Restart your terminal, or
   - Run: `source ~/.bashrc` (or `source ~/.zshrc`)

5. **Available Commands:**
   The following commands work with either method (replace `meteorix` with `python src/data/data_cli.py` if not using the alias):
   ```bash
   meteorix --help
   ```


## Discord Bot Integration

The project includes a Discord bot that inherits all CLI functionalities. The bot provides both mention-based commands and slash commands.

### Setup Instructions:

1. **Add Discord Bot Token to secrets.toml:**
   ```toml
   [bot_token]
   token = "YOUR_BOT_TOKEN"

   [channel_id]
   id = "YOUR_CHANNEL_ID"
   ```

2. **Run the Discord Bot:**
   ```bash
   python src/meteorix.py
   ```

### Using the Bot:

1. **Mention Commands:**
   ```
   @meteorix help           # Show all available commands
   @meteorix help <command> # Show detailed help for specific command
   @meteorix info          # Show available date range
   @meteorix who           # Show bot information
   ```

2. **Slash Commands:**
   Type `/` in Discord to see all available commands with descriptions.

The bot inherits all functionalities from the CLI tool and provides them through Discord's interface, making it easy to manage weather data and analysis directly from Discord.


#### File Structure

```
📦weather-dashboard
 ┣ 📂.devcontainer               // Dev container configuration
 ┣ 📂.github                     // GitHub workflows and actions
 ┃ ┗ 📂workflows
 ┃ ┃ ┗ 📄ci_cd.yml
 ┣ 📂.streamlit                  // Streamlit configuration files
 ┃ ┣ 📄config.toml                  // App configuration
 ┃ ┗ 📄secrets.toml                 // Secrets configuration
 ┣ 📂lib                         // Library and documentation files
 ┃ ┣ 📂fig                          // Plots and images
 ┃ ┃ ┣ 📂eda
 ┃ ┃ ┣ 📂ml
 ┃ ┃ ┣ 📂pca
 ┃ ┃ ┗ 📄banner.png
 ┃ ┣ 📄project_instructions.pdf
 ┃ ┣ 📄project_proposal.md
 ┃ ┗ 📄project_report.md
 ┣ 📂src                         // Source code files
 ┃ ┣ 📂components                   // Dashboard components
 ┃ ┣ 📂data                         // Data analysis and CLI scripts
 ┃ ┣ 📄app.py                       // Web app file
 ┃ ┗ 📄meteorix.py                  // Discord bot file
 ┣ 📄.gitignore
 ┣ 📄LICENSE
 ┣ 📄README.md
 ┗ 📄requirements.txt            // Python dependencies
 ```