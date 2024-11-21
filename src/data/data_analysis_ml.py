import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    average_precision_score,
    accuracy_score,
)
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold
import os
from sklearn.ensemble import RandomForestClassifier


def load_and_prepare_data(file_path, wind_threshold):
    # Load data
    df = pd.read_csv(file_path)
    df["tNow"] = pd.to_datetime(df["tNow"])

    # Add temporal features
    df["hour"] = df["tNow"].dt.hour
    df["day"] = df["tNow"].dt.day
    df["month"] = df["tNow"].dt.month

    # Calculate 3D wind speed
    df["3dSpeed_m_s"] = np.sqrt(df["u_m_s"] ** 2 + df["v_m_s"] ** 2 + df["w_m_s"] ** 2)

    selected_features = ["Press_Pa", "Elev_deg", "day", "Temp_C", "Hum_RH"]

    # Create target variable
    df["target"] = (df["3dSpeed_m_s"] >= wind_threshold).astype(int)

    print(f"\nThreshold: {wind_threshold:.2f} m/s")
    print("\nClass Distribution:")
    print(df["target"].value_counts(normalize=True))

    return df[selected_features], df["target"]


def evaluate_with_cv(X, y, model_name, model, n_splits=5):
    if len(np.unique(y)) < 2:
        print("Warning: Only one class present for threshold. Skipping evaluation.")
        return {
            "accuracy": 1.0,
            "roc_auc": 0.5,
            "class_distribution": f"Class 0: {sum(y==0)}, Class 1: {sum(y==1)}",
        }

    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    scores = {"accuracy": [], "roc_auc": [], "fold_distributions": []}

    print(f"\n{model_name} Cross-Validation Details:")
    for fold, (train_idx, test_idx) in enumerate(cv.split(X, y), 1):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Print class distribution for each fold
        train_dist = f"Train - Class 0: {sum(y_train==0)}, Class 1: {sum(y_train==1)}"
        test_dist = f"Test - Class 0: {sum(y_test==0)}, Class 1: {sum(y_test==1)}"
        print(f"\nFold {fold}:")
        print(f"Training set distribution: {train_dist}")
        print(f"Test set distribution: {test_dist}")

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train and predict
        model.fit(X_train_scaled, y_train)
        y_prob = model.predict_proba(X_test_scaled)[:, 1]

        # Calculate and print fold metrics
        fold_roc_auc = roc_auc_score(y_test, y_prob)
        print(f"Fold ROC-AUC: {fold_roc_auc:.3f}")

        scores["accuracy"].append(accuracy_score(y_test, model.predict(X_test_scaled)))
        scores["roc_auc"].append(fold_roc_auc)
        scores["fold_distributions"].append((train_dist, test_dist))

    # Print average metrics
    print(
        f"\nAverage ROC-AUC: {np.mean(scores['roc_auc']):.3f} ± {np.std(scores['roc_auc']):.3f}"
    )
    print(
        f"Average Accuracy: {np.mean(scores['accuracy']):.3f} ± {np.std(scores['accuracy']):.3f}"
    )

    return {
        k: np.mean(v) if k != "fold_distributions" else v for k, v in scores.items()
    }


def plot_roc_curves_for_threshold(
    lr_model, dt_model, rf_model, X_test, y_test, threshold, output_dir="lib/fig/ml/"
):
    plt.style.use("dark_background")

    lr_probs = lr_model.predict_proba(X_test)[:, 1]
    dt_probs = dt_model.predict_proba(X_test)[:, 1]
    rf_probs = rf_model.predict_proba(X_test)[:, 1]

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    lr_fpr, lr_tpr, _ = roc_curve(y_test, lr_probs)
    dt_fpr, dt_tpr, _ = roc_curve(y_test, dt_probs)
    rf_fpr, rf_tpr, _ = roc_curve(y_test, rf_probs)

    ax.plot(
        lr_fpr,
        lr_tpr,
        label=f"Logistic Regression (AUC = {roc_auc_score(y_test, lr_probs):.2f})",
    )
    ax.plot(
        dt_fpr,
        dt_tpr,
        label=f"Decision Tree (AUC = {roc_auc_score(y_test, dt_probs):.2f})",
    )
    ax.plot(
        rf_fpr,
        rf_tpr,
        label=f"Random Forest (AUC = {roc_auc_score(y_test, rf_probs):.2f})",
    )
    ax.plot([0, 1], [0, 1], "k--")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"ROC Curves Comparison (Threshold: {threshold:.2f} m/s)")
    ax.legend()
    plt.grid(True, alpha=0.2)
    plt.savefig(
        f"{output_dir}roc_curves_threshold_{threshold:.1f}.png",
        bbox_inches="tight",
        transparent=True,
    )
    plt.close()
    plt.style.use("default")  # Reset to default style


def plot_pr_curves_for_threshold(
    lr_model, dt_model, rf_model, X_test, y_test, threshold, output_dir="lib/fig/ml/"
):
    plt.style.use("dark_background")

    lr_probs = lr_model.predict_proba(X_test)[:, 1]
    dt_probs = dt_model.predict_proba(X_test)[:, 1]
    rf_probs = rf_model.predict_proba(X_test)[:, 1]

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    lr_precision, lr_recall, _ = precision_recall_curve(y_test, lr_probs)
    dt_precision, dt_recall, _ = precision_recall_curve(y_test, dt_probs)
    rf_precision, rf_recall, _ = precision_recall_curve(y_test, rf_probs)

    ax.plot(
        lr_recall,
        lr_precision,
        label=f"LR (AP = {average_precision_score(y_test, lr_probs):.2f})",
    )
    ax.plot(
        dt_recall,
        dt_precision,
        label=f"DT (AP = {average_precision_score(y_test, dt_probs):.2f})",
    )
    ax.plot(
        rf_recall,
        rf_precision,
        label=f"RF (AP = {average_precision_score(y_test, rf_probs):.2f})",
    )
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(f"Precision-Recall Curves (Threshold: {threshold:.2f} m/s)")
    ax.legend()
    plt.grid(True, alpha=0.2)
    plt.savefig(
        f"{output_dir}pr_curves_threshold_{threshold:.1f}.png",
        bbox_inches="tight",
        transparent=True,
    )
    plt.close()
    plt.style.use("default")  # Reset to default style


def plot_predictions_timeseries(
    df, lr_model, dt_model, rf_model, X_scaled, threshold_ms, output_dir="lib/fig/ml/"
):
    plt.style.use("dark_background")

    # Get predictions
    lr_predictions = lr_model.predict(X_scaled)
    dt_predictions = dt_model.predict(X_scaled)
    rf_predictions = rf_model.predict(X_scaled)

    # Get probabilities to see confidence levels
    lr_model.predict_proba(X_scaled)[:, 1]
    dt_model.predict_proba(X_scaled)[:, 1]
    rf_model.predict_proba(X_scaled)[:, 1]

    # Print prediction statistics
    print("\nPrediction Statistics:")
    for name, preds in [
        ("LR", lr_predictions),
        ("DT", dt_predictions),
        ("RF", rf_predictions),
    ]:
        n_positive = np.sum(preds == 1)
        print(
            f"{name} positive predictions: {n_positive} ({n_positive/len(preds)*100:.2f}%)"
        )

    ms_to_mph = 2.23694
    wind_speed_mph = df["3DSpeed_m_s"] * ms_to_mph
    threshold_mph = threshold_ms * ms_to_mph

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 18), sharex=True)
    fig.patch.set_alpha(0)

    # Logistic Regression plot
    ax1.patch.set_alpha(0)
    ax1.plot(df["tNow"], wind_speed_mph, color="gray", alpha=0.5, label="Wind Speed")
    high_wind_mask_lr = lr_predictions == 1
    ax1.scatter(
        df.loc[high_wind_mask_lr, "tNow"],
        wind_speed_mph[high_wind_mask_lr],
        color="cyan",
        alpha=0.6,
        label="LR Predicted High Wind",
    )
    ax1.axhline(
        y=threshold_mph,
        color="r",
        linestyle="--",
        label=f"Threshold ({threshold_mph:.1f} mph)",
    )
    ax1.set_ylabel("Wind Speed (mph)")
    ax1.set_title("Logistic Regression Predictions")
    ax1.legend()
    ax1.grid(True, alpha=0.2)

    # Decision Tree plot
    ax2.patch.set_alpha(0)
    ax2.plot(df["tNow"], wind_speed_mph, color="gray", alpha=0.5, label="Wind Speed")
    high_wind_mask_dt = dt_predictions == 1
    ax2.scatter(
        df.loc[high_wind_mask_dt, "tNow"],
        wind_speed_mph[high_wind_mask_dt],
        color="magenta",
        alpha=0.6,
        label="DT Predicted High Wind",
    )
    ax2.axhline(
        y=threshold_mph,
        color="r",
        linestyle="--",
        label=f"Threshold ({threshold_mph:.1f} mph)",
    )
    ax2.set_ylabel("Wind Speed (mph)")
    ax2.set_title("Decision Tree Predictions")
    ax2.legend()
    ax2.grid(True, alpha=0.2)

    # Random Forest plot
    ax3.patch.set_alpha(0)
    ax3.plot(df["tNow"], wind_speed_mph, color="gray", alpha=0.5, label="Wind Speed")
    high_wind_mask_rf = rf_predictions == 1
    ax3.scatter(
        df.loc[high_wind_mask_rf, "tNow"],
        wind_speed_mph[high_wind_mask_rf],
        color="yellow",
        alpha=0.6,
        label="RF Predicted High Wind",
    )
    ax3.axhline(
        y=threshold_mph,
        color="r",
        linestyle="--",
        label=f"Threshold ({threshold_mph:.1f} mph)",
    )
    ax3.set_xlabel("Time")
    ax3.set_ylabel("Wind Speed (mph)")
    ax3.set_title("Random Forest Predictions")
    ax3.legend()
    ax3.grid(True, alpha=0.2)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(
        f"{output_dir}wind_predictions_comparison.png",
        transparent=True,
        bbox_inches="tight",
    )
    plt.close()
    plt.style.use("default")


def evaluate_models(X_train, X_test, y_train, y_test, lr_model, dt_model, rf_model):
    """Basic evaluation of models before threshold analysis"""
    results = {}

    for name, model in [
        ("Logistic Regression", lr_model),
        ("Decision Tree", dt_model),
        ("Random Forest", rf_model),
    ]:
        # Train model
        model.fit(X_train, y_train)

        # Get predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        # Calculate metrics
        results[name] = {
            "accuracy": accuracy_score(y_test, y_pred),
            "roc_auc": roc_auc_score(y_test, y_prob),
            "classification_report": classification_report(y_test, y_pred),
        }

    return results


def main():
    # Create output directories
    os.makedirs("lib/fig/ml", exist_ok=True)

    # Load and prepare initial data
    print("\nInitial Model Evaluation...")
    df = pd.read_csv("src/data/merged_weather_data.csv")
    df["tNow"] = pd.to_datetime(df["tNow"])

    # Use a moderate threshold for initial evaluation
    X, y = load_and_prepare_data("src/data/merged_weather_data.csv", wind_threshold=5.0)
    X = np.array(X)
    y = np.array(y)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Initialize models
    lr_model = LogisticRegression(random_state=42, class_weight="balanced")
    dt_model = DecisionTreeClassifier(random_state=42, class_weight="balanced")
    rf_model = RandomForestClassifier(
        n_estimators=100, random_state=42, class_weight="balanced", n_jobs=-1
    )

    # Initial model evaluation
    initial_results = evaluate_models(
        X_train_scaled, X_test_scaled, y_train, y_test, lr_model, dt_model, rf_model
    )

    # Print initial results
    print("\nInitial Model Results (before threshold analysis):")
    for model_name, metrics in initial_results.items():
        print(f"\n{model_name}:")
        print(f"Accuracy: {metrics['accuracy']:.3f}")
        print(f"ROC-AUC: {metrics['roc_auc']:.3f}")
        print("\nClassification Report:")
        print(metrics["classification_report"])

    # Generate initial prediction plot
    X_scaled = scaler.transform(X)
    plot_predictions_timeseries(
        df,
        lr_model,
        dt_model,
        rf_model,
        X_scaled,
        5.0,
        output_dir="lib/fig/ml/threshold_initial_",
    )

    # Define thresholds
    thresholds = {
        "Very Light": 3.3,  # ~7.4 mph
        "Light": 5.0,  # ~11.2 mph
        "Moderate": 7.9,  # ~17.7 mph
        "Strong": 10.0,  # ~22.4 mph
        "Tropical Depression": 15.6,  # 35 mph
        # "Tropical Storm": 26.8,  # 60 mph (no data exist)
        # "Category 1": 33.5,  # 75 mph (no data exist)
    }

    results = []

    for name, threshold in thresholds.items():
        print(f"\nAnalyzing {name} threshold...")

        # Load and prepare data for this threshold
        X, y = load_and_prepare_data(
            "src/data/merged_weather_data.csv", wind_threshold=threshold
        )
        X = np.array(X)
        y = np.array(y)

        # Initialize models
        lr_model = LogisticRegression(random_state=42, class_weight="balanced")
        dt_model = DecisionTreeClassifier(random_state=42, class_weight="balanced")
        rf_model = RandomForestClassifier(
            n_estimators=100, random_state=42, class_weight="balanced", n_jobs=-1
        )

        # Evaluate with cross-validation
        lr_scores = evaluate_with_cv(X, y, "Logistic Regression", lr_model)
        dt_scores = evaluate_with_cv(X, y, "Decision Tree", dt_model)
        rf_scores = evaluate_with_cv(X, y, "Random Forest", rf_model)

        # Store results
        results.append(
            {
                "Threshold Name": name,
                "Threshold Value": threshold,
                "LR Accuracy": lr_scores["accuracy"],
                "LR ROC-AUC": lr_scores["roc_auc"],
                "DT Accuracy": dt_scores["accuracy"],
                "DT ROC-AUC": dt_scores["roc_auc"],
                "RF Accuracy": rf_scores["accuracy"],
                "RF ROC-AUC": rf_scores["roc_auc"],
            }
        )

        # Generate plots for this threshold
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        lr_model.fit(X_train_scaled, y_train)
        dt_model.fit(X_train_scaled, y_train)
        rf_model.fit(X_train_scaled, y_train)

        # Generate prediction time series plot for this threshold
        X_scaled = scaler.transform(X)
        plot_predictions_timeseries(
            df,
            lr_model,
            dt_model,
            rf_model,
            X_scaled,
            threshold,
            output_dir=f"lib/fig/ml/threshold_{name.lower()}_",
        )

        plot_roc_curves_for_threshold(
            lr_model, dt_model, rf_model, X_test_scaled, y_test, threshold
        )
        plot_pr_curves_for_threshold(
            lr_model, dt_model, rf_model, X_test_scaled, y_test, threshold
        )

    # Create results table
    results_df = pd.DataFrame(results)
    print("\nResults Summary:")
    print(results_df.to_string(index=False))

    # Plot model performance comparison
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    thresholds = results_df["Threshold Value"].values
    lr_auc = results_df["LR ROC-AUC"].values
    dt_auc = results_df["DT ROC-AUC"].values
    rf_auc = results_df["RF ROC-AUC"].values

    plt.plot(thresholds, lr_auc, "b-o", label="Logistic Regression")
    plt.plot(thresholds, dt_auc, "r-o", label="Decision Tree")
    plt.plot(thresholds, rf_auc, "g-o", label="Random Forest")
    plt.xlabel("Wind Speed Threshold (m/s)")
    plt.ylabel("ROC-AUC Score")
    plt.title("Model Performance vs Wind Speed Threshold")
    plt.legend()
    plt.grid(True, alpha=0.2)
    plt.savefig(
        "lib/fig/ml/model_performance_comparison.png",
        transparent=True,
        bbox_inches="tight",
    )
    plt.close()
    plt.style.use("default")  # Reset to default style


if __name__ == "__main__":
    main()
