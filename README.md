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

## MongoDB CLI Operations

The project includes a CLI tool for managing weather data and analysis results in MongoDB:

1. **Upload Weather Data:**
   ```bash
   # Upload single date
   python src/data/data_cli.py upload 2024_10_08
   
   # Upload date range
   python src/data/data_cli.py upload 2024_10_08 2024_10_10
   ```

2. **Run Data Analysis:**
   ```bash
   # Run EDA and PCA analysis
   python src/data/data_cli.py eda
   
   # Run ML analysis
   python src/data/data_cli.py ml
   ```

3. **Check Analysis Results:**
   ```bash
   # View contents of all analysis collections
   python src/data/data_cli.py check
   ```

4. **Delete Weather Data:**
   ```bash
   # Delete all weather data from MongoDB
   python src/data/data_cli.py delete
   ```


## File Structure

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
 ┃ ┣ 📂data                         // Data and analysis scripts
 ┃ ┗ 📄app.py                       // Main file
 ┣ 📄.gitignore
 ┣ 📄LICENSE
 ┣ 📄README.md
 ┗ 📄requirements.txt            // Python dependencies
 ```