from pathlib import Path

# Base directories
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
DATA_DIR = SRC_DIR / "data"
CSV_DIR = "/var/tmp/wx"
LIB_DIR = ROOT_DIR / "lib"

# Analysis directories
ANALYSIS_RESULTS_DIR = DATA_DIR / "data_analysis_result"
FIGURE_DIR = LIB_DIR / "fig"

# Figure subdirectories
ML_FIG_DIR = FIGURE_DIR / "ml"
PCA_FIG_DIR = FIGURE_DIR / "pca"
EDA_FIG_DIR = FIGURE_DIR / "eda"
BOT_FIGURE_DIR = FIGURE_DIR / "bot"

# Data file paths
WEATHER_DATA_PATH = DATA_DIR / "merged_weather_data.csv"

# Streamlit secrets path
STREAMLIT_SECRETS_PATH = ROOT_DIR / ".streamlit" / "secrets.toml"

# Create necessary directories
for directory in [ANALYSIS_RESULTS_DIR, ML_FIG_DIR, PCA_FIG_DIR, EDA_FIG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Version information
__version__ = "0.1.0"

__all__ = [
    "ROOT_DIR",
    "SRC_DIR",
    "DATA_DIR",
    "LIB_DIR",
    "ANALYSIS_RESULTS_DIR",
    "FIGURE_DIR",
    "ML_FIG_DIR",
    "PCA_FIG_DIR",
    "EDA_FIG_DIR",
    "WEATHER_DATA_PATH",
    "__version__",
]
