import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src import ANALYSIS_RESULTS_DIR  # noqa: E402


def load_and_prepare_data(file_path: str) -> tuple[pd.DataFrame, list]:
    """Load and prepare data for PCA analysis."""
    # Load data
    df = pd.read_csv(file_path)
    df["tNow"] = pd.to_datetime(df["tNow"])

    # Add temporal features
    df["hour"] = df["tNow"].dt.hour
    df["day"] = df["tNow"].dt.day

    # Update features list
    features = [
        "u_m_s",
        "v_m_s",
        "w_m_s",
        "2dSpeed_m_s",
        "Azimuth_deg",
        "Elev_deg",
        "Press_Pa",
        "Temp_C",
        "Hum_RH",
        "SonicTemp_C",
        "hour",
        "day",
    ]

    return df, features


def perform_pca_analysis(df: pd.DataFrame, features: list) -> tuple:
    """Perform PCA analysis and save results."""
    # Standardize the features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[features])

    # Perform PCA
    pca = PCA()
    pca.fit_transform(scaled_features)

    # Calculate explained variance ratio
    explained_variance_ratio = pca.explained_variance_ratio_
    cumulative_variance_ratio = np.cumsum(explained_variance_ratio)

    # Get component loadings
    loadings = pd.DataFrame(
        pca.components_.T,
        columns=[f"PC{i+1}" for i in range(len(features))],
        index=features,
    )

    # Save PCA data to JSON
    pca_data = {
        "explained_variance_ratio": explained_variance_ratio.tolist(),
        "cumulative_variance_ratio": cumulative_variance_ratio.tolist(),
        "loadings": loadings.to_dict(),
        # Add 3D biplot data
        "biplot_data": {
            "features": features,
            "pc_coordinates": pca.components_[:3].T.tolist(),  # First 3 PCs for 3D
            "explained_variance_3d": explained_variance_ratio[:3].tolist(),
            "feature_names": features,
        },
    }

    # Update the save path to use ANALYSIS_RESULTS_DIR
    output_file = ANALYSIS_RESULTS_DIR / "pca_data.json"
    with open(output_file, "w") as f:
        json.dump(pca_data, f, indent=2)

    return pca, loadings, explained_variance_ratio, cumulative_variance_ratio


def plot_pca_results(
    loadings,
    explained_variance_ratio,
    cumulative_variance_ratio,
):
    """Generate and save PCA visualization plots."""
    # Update output directory
    output_dir = Path("lib/fig/pca/")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set style
    plt.style.use("dark_background")

    # Plot explained variance
    plt.figure(figsize=(10, 6))
    plt.plot(
        range(1, len(explained_variance_ratio) + 1), cumulative_variance_ratio, "bo-"
    )
    plt.xlabel("Number of Components")
    plt.ylabel("Cumulative Explained Variance Ratio")
    plt.title("PCA Explained Variance")
    plt.grid(True, alpha=0.3)
    plt.savefig(
        output_dir / "pca_explained_variance.png", bbox_inches="tight", transparent=True
    )
    plt.close("all")

    # Plot loadings heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(loadings, annot=True, cmap="coolwarm", center=0)
    plt.title("PCA Component Loadings")
    plt.tight_layout()
    plt.savefig(output_dir / "pca_loadings.png", bbox_inches="tight", transparent=True)
    plt.close("all")


def analyze_temporal_importance(df, features, sequence_length=10):
    # Create sequences
    def create_sequences(data, seq_length):
        sequences = []
        for i in range(len(data) - seq_length):
            sequence = data[i : (i + seq_length)]
            # Flatten the sequence into a single feature vector
            sequences.append(sequence.flatten())
        return np.array(sequences)

    # Prepare sequential data
    X = create_sequences(df[features].values, sequence_length)
    y = df["3DSpeed_m_s"].values[sequence_length:]

    # Split maintaining temporal order
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # Use RandomForestRegressor directly
    model = RandomForestRegressor(
        n_estimators=50, max_depth=10, n_jobs=-1, random_state=42
    )

    # Fit the model
    model.fit(X_train, y_train)

    # Get feature importance for each time step
    feature_importance = pd.DataFrame(
        {
            "feature": [
                f"{feat}_t{t}" for t in range(sequence_length) for feat in features
            ],
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    return model, feature_importance, X_train, X_test, y_train, y_test


def main():
    print("Starting analysis...")

    # Load and prepare data
    df, features = load_and_prepare_data("src/data/merged_weather_data.csv")
    print("Data loaded successfully")

    # Perform PCA analysis
    pca, loadings, explained_variance_ratio, cumulative_variance_ratio = (
        perform_pca_analysis(df, features)
    )
    print("PCA analysis completed")

    # Plot PCA results
    plot_pca_results(loadings, explained_variance_ratio, cumulative_variance_ratio)
    print("Plots generated and saved")

    # Print results
    print("\nPCA Analysis Results:")

    # Create and print explained variance table
    variance_df = pd.DataFrame(
        {
            "Principal Component": [
                f"PC{i+1}" for i in range(len(explained_variance_ratio))
            ],
            "Individual Variance Explained": explained_variance_ratio,
            "Cumulative Variance Explained": cumulative_variance_ratio,
        }
    )
    variance_df = variance_df.set_index("Principal Component")
    variance_df = variance_df.round(4)
    print("\nExplained Variance Table:")
    print(variance_df.to_string())

    # Print loadings table with better formatting
    print("\nComponent Loadings Table:")
    loadings_formatted = loadings.round(4)
    print(loadings_formatted.to_string())

    # Print top contributing features for each principal component
    print("\nTop 3 Contributing Features for each Principal Component:")
    for pc in loadings.columns[:3]:  # First 3 PCs
        top_features = loadings[pc].abs().sort_values(ascending=False).head(3)
        print(f"\n{pc}:")
        for feat, value in top_features.items():
            print(f"  {feat}: {value:.4f}")

    # # Analyze temporal importance
    # model, feature_importance, X_train, X_test, y_train, y_test = (
    #     analyze_temporal_importance(df, features)
    # )
    # print("Temporal importance analysis completed")

    # print("\nTemporal Importance Analysis:")
    # print(f"Model: {model}")
    # print(f"R² Score: {model.score(X_test, y_test):.4f}")

    # # Print top 10 most important temporal features
    # print("\nTop 10 Most Important Temporal Features:")
    # print(feature_importance.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
