import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any


class WeatherDataPreprocessor:
    """Class to handle weather data preprocessing and analysis."""

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)

    def load_weather_data(self, date_str: str) -> pd.DataFrame:
        """Load weather data for a specific date."""
        file_path = self.data_dir / f"{date_str}_weather_station_data.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"No data file found for date: {date_str}")

        df = pd.read_csv(file_path)
        df["tNow"] = pd.to_datetime(df["tNow"])
        return df

    @staticmethod
    def get_stats(column: pd.Series) -> Dict[str, float]:
        """Calculate statistics for a column."""
        return {
            "median": float(np.median(column)),
            "mean": float(np.mean(column)),
            "min": float(np.min(column)),
            "max": float(np.max(column)),
            "range": float(np.ptp(column)),
        }

    def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze weather data and return statistics."""
        stats = {
            col: self.get_stats(df[col])
            for col in df.columns
            if col not in ["tNow", "Error"]
        }

        error_rows = df[df["Error"] > 0.0]

        return {
            "statistics": stats,
            "time_range": {
                "start": df["tNow"].min().isoformat(),
                "end": df["tNow"].max().isoformat(),
                "duration": str(df["tNow"].max() - df["tNow"].min()),
            },
            "total_errors": len(error_rows),
            "error_details": [
                {
                    "timestamp": row["tNow"].isoformat(),
                    "error_value": float(row["Error"]),
                }
                for _, row in error_rows.iterrows()
            ],
        }

    def print_analysis_results(self, results: Dict[str, Any]) -> None:
        """Print analysis results in a formatted way."""
        print("\nWeather Data Analysis Results")
        print("=" * 30)

        print("\nTime Range:")
        print(f"Start: {results['time_range']['start']}")
        print(f"End: {results['time_range']['end']}")
        print(f"Duration: {results['time_range']['duration']}")

        print("\nVariable Statistics:")
        for column, stats in results["statistics"].items():
            print(f"\n{column}:")
            for stat_name, value in stats.items():
                print(f"  {stat_name}: {value:.4f}")

        print("\nError Analysis:")
        print(f"Total errors: {results['total_errors']}")
        if results["error_details"]:
            print("\nDetailed Error List:")
            for error in results["error_details"]:
                print(f"Time: {error['timestamp']}, Value: {error['error_value']}")


def main(date_str: str = "2024_10_08"):
    """Run preprocessing analysis for a specific date."""
    try:
        preprocessor = WeatherDataPreprocessor("src/data")
        df = preprocessor.load_weather_data(date_str)
        results = preprocessor.analyze_data(df)
        preprocessor.print_analysis_results(results)
    except Exception as e:
        print(f"Error during preprocessing: {str(e)}")


if __name__ == "__main__":
    main()
