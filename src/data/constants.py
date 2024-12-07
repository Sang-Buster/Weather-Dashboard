from pathlib import Path

DATA_DIR = Path(__file__).parent
ANALYSIS_RESULTS_DIR = DATA_DIR / "data_analysis_result"

# Create directories if they don't exist
ANALYSIS_RESULTS_DIR.mkdir(exist_ok=True)
