import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json


# Read the CSV file
def load_weather_data(file_path):
    df = pd.read_csv(file_path)
    # Convert timestamp to datetime
    df["tNow"] = pd.to_datetime(df["tNow"])
    return df


def analyze_wind_patterns(df):
    # Calculate basic statistics for wind components
    wind_stats = {
        "Wind Speed (2D)": df["2dSpeed_m_s"].describe(),
        "Wind Speed (3D)": df["3DSpeed_m_s"].describe(),
        "Wind Direction": df["Azimuth_deg"].describe(),
        "Vertical Wind": df["w_m_s"].describe(),
    }

    # Calculate wind gustiness (standard deviation of wind speed)
    wind_gustiness = df["3DSpeed_m_s"].rolling(window=10).std()

    # Calculate wind variability
    wind_direction_variability = df["Azimuth_deg"].rolling(window=10).std()

    # Add wind rose analysis
    wind_rose_data = pd.DataFrame(
        {"speed": df["3DSpeed_m_s"], "direction": df["Azimuth_deg"]}
    )

    return wind_stats, wind_gustiness, wind_direction_variability, wind_rose_data


def analyze_atmospheric_conditions(df):
    # Calculate correlations between parameters
    atmos_params = ["Press_Pa", "Temp_C", "Hum_RH", "3DSpeed_m_s"]
    correlation_matrix = df[atmos_params].corr()

    # Look for rapid pressure changes (potential hurricane indicator)
    pressure_change = df["Press_Pa"].diff()

    return correlation_matrix, pressure_change


def set_dark_style():
    # Set dark style for all plots
    plt.style.use("dark_background")

    # Additional customization for dark theme with transparency
    plt.rcParams.update(
        {
            "axes.facecolor": "none",
            "figure.facecolor": "none",
            "savefig.facecolor": "none",
            "text.color": "white",
            "axes.labelcolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
        }
    )


def create_and_save_visualizations(df, output_dir="lib/fig/eda/"):
    # Create output directories if they don't exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("src/data/data_analysis_result", exist_ok=True)

    # Set dark style
    set_dark_style()

    # Common figure parameters
    fig_params = {
        "figsize": (10, 8),
        "dpi": 300,
        "facecolor": "none",
        "edgecolor": "none",
    }

    # Common save parameters
    save_params = {
        "dpi": 300,
        "bbox_inches": "tight",
        "transparent": True,
        "facecolor": "none",
        "edgecolor": "none",
    }

    # Save correlation matrix to JSON
    correlation_vars = [
        "3DSpeed_m_s",
        "Azimuth_deg",
        "Elev_deg",
        "Press_Pa",
        "Temp_C",
        "Hum_RH",
    ]
    correlation_data = df[correlation_vars].corr().round(4).to_dict()

    with open("src/data/data_analysis_result/correlation_data.json", "w") as f:
        json.dump(correlation_data, f, indent=2)

    # 1. Correlation Matrix
    plt.figure(**fig_params)
    sns.heatmap(df[correlation_vars].corr(), annot=True, cmap="coolwarm")
    plt.tight_layout()
    plt.savefig(f"{output_dir}correlation_matrix.png", **save_params)
    plt.close()

    # 2. Wind Speed vs Temperature
    plt.figure(**fig_params)
    sns.scatterplot(
        data=df, x="Temp_C", y="3DSpeed_m_s", hue="Hum_RH", palette="viridis"
    )
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Wind Speed (m/s)")
    plt.legend(title="Relative Humidity (%)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}wind_speed_vs_temp.png", **save_params)
    plt.close()

    # 3. Pressure vs Wind Speed
    plt.figure(**fig_params)
    scatter = plt.scatter(
        df["Press_Pa"], df["3DSpeed_m_s"], c=df["Temp_C"], cmap="viridis", alpha=0.6
    )
    plt.colorbar(scatter, label="Temperature (°C)")
    plt.xlabel("Pressure (Pa)")
    plt.ylabel("Wind Speed (m/s)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}pressure_vs_wind_speed.png", **save_params)
    plt.close()

    # 4. Wind Speed vs Elevation Angle
    plt.figure(**fig_params)
    sns.scatterplot(data=df, x="Elev_deg", y="3DSpeed_m_s", alpha=0.5)
    plt.xlabel("Elevation Angle (degrees)")
    plt.ylabel("Wind Speed (m/s)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}wind_speed_vs_elevation.png", **save_params)
    plt.close()

    # 5. Pressure vs Temperature
    plt.figure(**fig_params)
    scatter = plt.scatter(
        df["Press_Pa"], df["Temp_C"], c=df["3DSpeed_m_s"], cmap="viridis", alpha=0.6
    )
    plt.colorbar(scatter, label="Wind Speed (m/s)")
    plt.xlabel("Pressure (Pa)")
    plt.ylabel("Temperature (°C)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}pressure_vs_temp.png", **save_params)
    plt.close()

    # 6. Vertical Wind vs Humidity
    plt.figure(**fig_params)
    scatter = plt.scatter(
        df["Hum_RH"], df["w_m_s"], c=df["Temp_C"], cmap="viridis", alpha=0.6
    )
    plt.colorbar(scatter, label="Temperature (°C)")
    plt.xlabel("Humidity (%)")
    plt.ylabel("Vertical Wind Speed (m/s)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}vertical_wind_vs_humidity.png", **save_params)
    plt.close()

    # 7. 2D vs 3D Wind Speed
    plt.figure(**fig_params)
    sns.scatterplot(
        data=df,
        x="2dSpeed_m_s",
        y="3DSpeed_m_s",
        hue="Elev_deg",
        palette="viridis",
        alpha=0.6,
    )
    plt.xlabel("2D Wind Speed (m/s)")
    plt.ylabel("3D Wind Speed (m/s)")
    plt.legend(title="Elevation Angle (°)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}2d_vs_3d_wind_speed.png", **save_params)
    plt.close()

    # 8. Wind Speed vs Temperature Difference
    plt.figure(**fig_params)
    df["temp_diff"] = df["SonicTemp_C"] - df["Temp_C"]
    sns.scatterplot(
        data=df,
        x="temp_diff",
        y="3DSpeed_m_s",
        hue="Press_Pa",
        palette="viridis",
        alpha=0.6,
    )
    plt.xlabel("Temperature Difference (Sonic - Regular) (°C)")
    plt.ylabel("Wind Speed (m/s)")
    plt.legend(title="Pressure (Pa)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}wind_speed_vs_temp_diff.png", **save_params)
    plt.close()

    # 9. Horizontal Wind vs Humidity
    plt.figure(**fig_params)
    scatter = plt.scatter(
        df["Hum_RH"], df["2dSpeed_m_s"], c=df["Temp_C"], cmap="viridis", alpha=0.6
    )
    plt.colorbar(scatter, label="Temperature (°C)")
    plt.xlabel("Humidity (%)")
    plt.ylabel("Horizontal Wind Speed (m/s)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}horizontal_wind_vs_humidity.png", **save_params)
    plt.close()


def perform_additional_analysis(df):
    # 1. Extreme value analysis
    extremes = {
        "Wind Speed 99th percentile": df["3DSpeed_m_s"].quantile(0.99),
        "Max vertical wind": df["w_m_s"].abs().max(),
        "Sustained high winds": df["3DSpeed_m_s"].rolling(window=30).mean().max(),
    }

    # 2. Stability analysis using temperature gradients
    df["temp_gradient"] = df["Temp_C"].diff().rolling(window=10).mean()
    stability_correlation = df["temp_gradient"].corr(df["w_m_s"])

    # 3. Wind shear analysis
    df["wind_shear"] = (
        np.sqrt(df["u_m_s"].diff() ** 2 + df["v_m_s"].diff() ** 2)
        / df["Elev_deg"].abs()
    )

    # 4. Gust factor analysis
    df["gust_factor"] = df["3DSpeed_m_s"] / df["3DSpeed_m_s"].rolling(window=600).mean()

    return {
        "extremes": extremes,
        "stability_correlation": stability_correlation,
        "mean_wind_shear": df["wind_shear"].mean(),
        "max_gust_factor": df["gust_factor"].max(),
    }


def main():
    # Load the data
    df = load_weather_data("src/data/merged_weather_data.csv")

    # Create and save individual plots
    create_and_save_visualizations(df, output_dir="lib/fig/eda/")

    # Print correlation matrix
    correlation_vars = [
        "3DSpeed_m_s",
        "Azimuth_deg",
        "Elev_deg",
        "Press_Pa",
        "Temp_C",
        "Hum_RH",
    ]
    correlation_matrix = df[correlation_vars].corr()
    print("\nCorrelation Matrix:")
    print(correlation_matrix.round(3))

    # Print wind statistics by quadrant (with warning fixed)
    print("\nDescriptive Statistics by Wind Direction Quadrant:")
    df["direction_quadrant"] = pd.cut(
        df["Azimuth_deg"],
        bins=[0, 90, 180, 270, 360],
        labels=["N-E", "E-S", "S-W", "W-N"],
    )
    print(df.groupby("direction_quadrant")["3DSpeed_m_s"].describe())

    # Analyze wind patterns
    analyze_wind_patterns(df)

    # Perform and print additional analysis
    analysis_results = perform_additional_analysis(df)
    print("\nAdditional Analysis Results:")
    print("Extreme Value Analysis:")
    for key, value in analysis_results["extremes"].items():
        print(f"{key}: {value:.2f}")
    print(
        f"\nTemperature-Vertical Wind Stability Correlation: {analysis_results['stability_correlation']:.3f}"
    )
    print(f"Mean Wind Shear: {analysis_results['mean_wind_shear']:.3f}")
    print(f"Maximum Gust Factor: {analysis_results['max_gust_factor']:.3f}")

    # Additional statistical analysis
    print("\nDescriptive Statistics by Wind Direction Quadrant:")
    df["direction_quadrant"] = pd.cut(
        df["Azimuth_deg"],
        bins=[0, 90, 180, 270, 360],
        labels=["N-E", "E-S", "S-W", "W-N"],
    )
    print(df.groupby("direction_quadrant")["3DSpeed_m_s"].describe())

    # Perform Kolmogorov-Smirnov test for wind speed distribution
    print("\nKolmogorov-Smirnov test for wind speed normality:")
    ks_statistic, p_value = stats.kstest(df["3DSpeed_m_s"], "norm")
    print(f"KS statistic: {ks_statistic:.4f}")
    print(f"p-value: {p_value:.4f}")


if __name__ == "__main__":
    main()
