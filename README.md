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

5. **Run the Streamlit application:**
   ```bash
   streamlit run src/app.py
   ```

## Development Instructions

1. **Code Linting and Formatting:**
   ```bash
   ruff check src
   ruff format src
   ```


## File Structure

```
📦weather-dashboard
 ┣ 📂.devcontainer          // Dev container configuration
 ┣ 📂.github                // GitHub workflows and actions
 ┃ ┗ 📂workflows
 ┃ ┃ ┗ 📜ci_cd.yml
 ┣ 📂.streamlit             // Streamlit configuration files
 ┃ ┣ 📜config.toml             // App configuration
 ┃ ┗ 📜secrets.toml            // Secrets configuration
 ┣ 📂lib                    // Library and documentation files
 ┃ ┣ 📂fig                     // Plots and images
 ┃ ┃ ┣ 📂eda
 ┃ ┃ ┣ 📂ml
 ┃ ┃ ┣ 📂pca
 ┃ ┃ ┗ 📜banner.png
 ┃ ┣ 📜project_instructions.pdf
 ┃ ┣ 📜project_proposal.md
 ┃ ┗ 📜project_report.md
 ┣ 📂src                    // Source code files
 ┃ ┣ 📂components              // Dashboard components
 ┃ ┣ 📂data                    // Data and analysis scripts
 ┃ ┃ ┣ 📂data_analysis_result
 ┃ ┗ 📜app.py                  // Main file
 ┣ 📜.gitignore
 ┣ 📜LICENSE
 ┣ 📜README.md
 ┗ 📜requirements.txt       // Python dependencies
 ```