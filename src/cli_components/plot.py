import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import io
from pathlib import Path
from rich import print as rprint
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

from src import CSV_DIR, BOT_FIGURE_DIR

DATA_DIR = Path(CSV_DIR)
Path(BOT_FIGURE_DIR).mkdir(parents=True, exist_ok=True)


def calculate_dewpoint(temp_c, relative_humidity):
    """Calculate dew point temperature using simple approximation formula."""
    return temp_c - ((100 - relative_humidity) / 5.0)


def celsius_to_fahrenheit(temp_c):
    """Convert Celsius to Fahrenheit."""
    return (temp_c * 9 / 5) + 32


def ms_to_mph(speed_ms):
    """Convert meters per second to miles per hour."""
    return speed_ms * 2.23694


def categorize_wind_direction(degrees):
    """Convert azimuth degrees to cardinal directions."""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((degrees + 22.5) % 360 // 45)
    return directions[idx]


def create_wind_rose(ax, wind_speed, wind_dir, title="Wind Rose"):
    """Create wind rose using matplotlib."""
    # Set up directional bins (every 45 degrees)
    dir_bins = np.arange(-11.25, 360 - 11.25 + 22.5, 22.5)
    dir_labels = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    # Set up more speed bins (in mph)
    speed_bins = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, float("inf")]
    speed_labels = [
        "0-5",
        "5-10",
        "10-15",
        "15-20",
        "20-25",
        "25-30",
        "30-35",
        "35-40",
        "40-45",
        "45-50",
        "50-55",
        "55-60",
        "60+",
    ]

    # Extended color palette with more distinct colors for higher speeds
    colors = [
        "#2ecc71",  # Light breeze (green)
        "#3498db",  # Gentle breeze (blue)
        "#f1c40f",  # Moderate breeze (yellow)
        "#e67e22",  # Fresh breeze (orange)
        "#e74c3c",  # Strong breeze (red)
        "#9b59b6",  # Near gale (purple)
        "#34495e",  # Gale (dark blue)
        "#c0392b",  # Strong gale (dark red)
        "#d35400",  # Storm (dark orange)
        "#8e44ad",  # Violent storm (dark purple)
        "#ff1493",  # Deep pink for 50-55
        "#00ffff",  # Cyan for 55-60
        "#ff0000",  # Bright red for 60+
    ]

    # Convert angles to 0-360
    wind_dir = wind_dir % 360

    # Initialize frequency array
    freq = np.zeros((len(speed_bins) - 1, len(dir_bins) - 1))

    # Count frequencies
    for i in range(len(speed_bins) - 1):
        if i == len(speed_bins) - 2:  # Last bin (60+)
            mask = wind_speed >= speed_bins[i]
        else:
            mask = (wind_speed >= speed_bins[i]) & (wind_speed < speed_bins[i + 1])
        dir_hist, _ = np.histogram(wind_dir[mask], bins=dir_bins)
        freq[i] = dir_hist

    # Convert to percentages
    freq = freq * 100.0 / len(wind_speed)

    # Plot each speed bin
    width = np.pi / 8
    theta = np.radians(np.arange(0, 360, 22.5))

    # Keep track of which speed bins have data
    active_bins = []
    active_colors = []
    active_labels = []

    for i in range(len(speed_bins) - 1):
        if np.any(freq[i] > 0):  # Only plot and add to legend if bin has data
            ax.bar(
                theta,
                freq[i],
                width=width,
                bottom=np.sum(freq[:i], axis=0),
                color=colors[i],
                label=f"{speed_labels[i]} mph",
                edgecolor="white",
                alpha=0.8,
            )
            active_bins.append(i)
            active_colors.append(colors[i])
            active_labels.append(f"{speed_labels[i]} mph")

    # Customize the plot
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)  # clockwise
    ax.set_thetagrids(np.arange(0, 360, 22.5), dir_labels)
    ax.set_title(title)

    # Only show legend if there are active bins
    if active_bins:
        ax.legend(
            title="Wind Speed (mph)",
            bbox_to_anchor=(1.2, -0.1),  # Moved to bottom right
            loc="lower right",
        )


def create_wind_plots(
    combined_df, start_date, end_date=None
) -> tuple[plt.Figure, plt.Figure]:
    """Create wind-specific plots: time series and wind rose."""
    # Create first figure for time series with arrows
    fig1 = plt.figure(figsize=(15, 12))

    # Create subplot grid with specific spacing
    gs = fig1.add_gridspec(
        2,
        1,
        height_ratios=[1, 1],
        top=0.95,  # Leave space for title
        bottom=0.08,  # Leave space for x-labels
        left=0.1,  # Leave space for y-labels
        right=0.9,  # Leave space for legend
        hspace=0.25,
    )  # Space between plots

    # Create two subplots
    ax1 = fig1.add_subplot(gs[0])  # U/V components plot
    ax2 = fig1.add_subplot(gs[1])  # Wind speed and direction plot

    # Convert wind speeds to mph
    u_mph = ms_to_mph(combined_df["u_m_s"])
    v_mph = ms_to_mph(combined_df["v_m_s"])
    wind_speed_mph = ms_to_mph(combined_df["3DSpeed_m_s"])

    # Plot U/V components
    ax1.plot(
        combined_df["tNow"], u_mph, color="red", alpha=0.7, label="U (E-W) Component"
    )
    ax1.plot(
        combined_df["tNow"], v_mph, color="green", alpha=0.7, label="V (N-S) Component"
    )
    ax1.set_ylabel("Wind Component Speed (mph)")
    ax1.legend()
    ax1.grid(True)
    ax1.set_xticklabels([])  # Hide x-axis labels for top plot
    ax1.tick_params(axis="x", length=0)  # Hide x-axis ticks

    # Plot wind speed as line
    ax2.plot(
        combined_df["tNow"], wind_speed_mph, color="blue", alpha=0.3, label="Wind Speed"
    )
    ax2.set_ylabel("Wind Speed (mph)")

    # Add arrows for direction
    n = max(1, len(combined_df) // 200)  # Increased sampling to show more arrows
    times = combined_df["tNow"][::n]
    speeds = wind_speed_mph[::n]
    directions = np.radians(combined_df["Azimuth_deg"][::n])

    # Plot arrows using Azimuth directly
    q = ax2.quiver(
        times,
        speeds,
        np.sin(directions + np.pi),  # X component
        np.cos(directions + np.pi),  # Y component
        scale=50,  # Scale for arrow size
        width=0.002,  # Arrow width
        headwidth=3,  # Arrow head width
        headlength=5,  # Arrow head length
        headaxislength=4.5,  # Arrow head axis length
        color="darkblue",
        alpha=0.7,
    )

    # Move the reference arrow to top left corner
    ax2.quiverkey(q, 0.032, 0.88, 1, "Wind Direction", labelpos="E", coordinates="axes")

    ax2.grid(True)
    ax2.legend(
        loc="upper left"
    )  # Keep legend in upper left, but it will appear after the quiverkey
    ax2.tick_params(axis="x", rotation=45)

    # Remove tight_layout call and instead add title directly
    if end_date:
        fig1.suptitle(f"Wind Patterns: {start_date} to {end_date}", y=0.98)
    else:
        fig1.suptitle(f"Wind Patterns: {start_date}", y=0.98)

    # Create second figure for wind rose - make it square with more legend space
    fig2 = plt.figure(figsize=(10, 10))
    ax2 = fig2.add_subplot(111, projection="polar")

    create_wind_rose(ax2, wind_speed_mph, combined_df["Azimuth_deg"].values)

    # Adjust layout with more space for legend
    fig2.subplots_adjust(right=0.8)  # More space on right for legend

    return fig1, fig2


def create_3d_wind_plot(combined_df, start_date, end_date=None) -> plt.Figure:
    """Create 3D surface plot of wind speed over time and direction."""
    # Create wider and taller figure with better margins
    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_axes([0.1, 0.15, 0.8, 0.75], projection="3d")

    # Convert wind speed to mph
    wind_speed_mph = ms_to_mph(combined_df["3DSpeed_m_s"])

    # Create direction and time meshgrid
    dir_bins = np.linspace(0, 360, 73)  # 5-degree bins

    # Use simple indices for the time axis calculations
    time_bins = np.linspace(0, len(combined_df) - 1, 100)

    Dir, Time = np.meshgrid(dir_bins, time_bins)
    Speed = np.zeros_like(Dir)

    # For each time bin, interpolate speeds across directions
    for i, t in enumerate(time_bins):
        idx = int(round(t))
        if idx >= len(combined_df):
            idx = len(combined_df) - 1

        actual_dir = combined_df["Azimuth_deg"].iloc[idx]
        actual_speed = wind_speed_mph.iloc[idx]

        sigma = 15  # Width of gaussian in degrees
        dir_diff = np.minimum(
            np.abs(Dir[i] - actual_dir), np.abs(Dir[i] - (actual_dir + 360))
        )
        dir_diff = np.minimum(dir_diff, np.abs(Dir[i] - (actual_dir - 360)))
        Speed[i] = actual_speed * np.exp(-(dir_diff**2) / (2 * sigma**2))

    # Create the surface plot
    surf = ax.plot_surface(
        Time, Dir, Speed, cmap="coolwarm", linewidth=0, antialiased=True
    )

    # Adjust the plot aspect ratio
    ax.get_proj = lambda: np.dot(Axes3D.get_proj(ax), np.diag([1.3, 1.1, 1.1, 1]))

    # Set x-ticks to show actual times
    num_ticks = min(10, len(combined_df) // 100)
    tick_indices = np.linspace(0, len(combined_df) - 1, num_ticks)
    ax.set_xticks(tick_indices)

    # Get the actual datetime strings for the ticks
    tick_labels = [
        combined_df["tNow"].iloc[int(idx)].strftime("%m-%d %H:%M")
        for idx in tick_indices
    ]

    ax.set_xticklabels(tick_labels, rotation=45, ha="right", va="top")

    # Adjust the view
    ax.view_init(elev=20, azim=-60)

    # Set labels with adjusted padding
    ax.set_xlabel("Time", labelpad=30)
    ax.set_ylabel("Wind Direction", labelpad=10)
    ax.set_zlabel("Wind Speed (mph)", labelpad=5)

    # Set direction ticks
    dir_ticks = np.arange(0, 361, 45)
    dir_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
    ax.set_yticks(dir_ticks)
    ax.set_yticklabels(dir_labels)

    # Adjust z-axis limits
    max_speed = wind_speed_mph.max()
    ax.set_zlim(0, max_speed * 1.1)

    # Add title
    if end_date:
        title = f"3D Wind Pattern: {start_date} to {end_date}"
    else:
        title = f"3D Wind Pattern: {start_date}"
    ax.set_title(title, pad=10)

    # Add centered colorbar with more space and lower position
    plt.subplots_adjust(bottom=0.3)  # Increased bottom margin even more
    cbar_ax = fig.add_axes(
        [0.3, 0.05, 0.4, 0.03]
    )  # Moved colorbar much lower (y position now 0.05)
    fig.colorbar(surf, cax=cbar_ax, orientation="horizontal", label="Wind Speed (mph)")

    return fig


def create_weather_plot(
    start_date: str, end_date: str = None, save_locally: bool = False
) -> tuple[
    tuple[str, str, str, str],
    tuple[io.BytesIO, io.BytesIO, io.BytesIO, io.BytesIO],
    tuple[Path, Path, Path, Path],
]:
    """Create weather plots and return filename and buffer."""
    try:
        # Generate list of dates
        start = datetime.strptime(start_date, "%Y_%m_%d")
        end = datetime.strptime(end_date, "%Y_%m_%d") if end_date else start

        # Initialize empty list to store DataFrames
        dfs = []

        # Read and combine data
        current = start
        while current <= end:
            date_str = current.strftime("%Y_%m_%d")
            filename = DATA_DIR / f"{date_str}_weather_station_data.csv"

            if not filename.exists():
                rprint(f"[red]Warning: File not found for {date_str}[/red]")
            else:
                df = pd.read_csv(filename)
                df["tNow"] = pd.to_datetime(df["tNow"])
                dfs.append(df)

            current += pd.Timedelta(days=1)

        if not dfs:
            raise FileNotFoundError("No data files found for the specified date range")

        # Combine all DataFrames
        combined_df = pd.concat(dfs, ignore_index=True)

        # Calculate dew point and convert temperatures
        combined_df["Dew_Point_C"] = calculate_dewpoint(
            combined_df["Temp_C"], combined_df["Hum_RH"]
        )

        # Convert to Fahrenheit
        combined_df["Temp_F"] = celsius_to_fahrenheit(combined_df["Temp_C"])
        combined_df["Dew_Point_F"] = celsius_to_fahrenheit(combined_df["Dew_Point_C"])

        # Create four figures
        fig1 = plt.figure(figsize=(12, 10))
        gs = fig1.add_gridspec(
            3, 1, height_ratios=[1, 1, 1], hspace=0.4
        )  # Increased hspace

        # Plot temperature and dew point in Fahrenheit
        ax1 = fig1.add_subplot(gs[0])
        ax1.plot(
            combined_df["tNow"], combined_df["Temp_F"], label="Temperature", color="red"
        )
        ax1.plot(
            combined_df["tNow"],
            combined_df["Dew_Point_F"],
            label="Dew Point",
            color="blue",
        )
        ax1.set_ylabel("Temperature (°F)")
        ax1.legend()
        ax1.grid(True)
        ax1.set_xticklabels([])  # Hide x-axis labels
        ax1.tick_params(axis="x", length=0)  # Hide x-axis ticks

        # Plot humidity
        ax2 = fig1.add_subplot(gs[1])
        ax2.plot(combined_df["tNow"], combined_df["Hum_RH"], color="green")
        ax2.set_ylabel("Relative Humidity (%)")
        ax2.grid(True)
        ax2.set_xticklabels([])  # Hide x-axis labels
        ax2.tick_params(axis="x", length=0)  # Hide x-axis ticks

        # Plot pressure
        ax3 = fig1.add_subplot(gs[2])
        ax3.plot(
            combined_df["tNow"], combined_df["Press_Pa"] / 100, color="purple"
        )  # Convert Pa to hPa
        ax3.set_ylabel("Pressure (hPa)")
        ax3.grid(True)

        # Format x-axis for bottom subplot only
        ax3.tick_params(axis="x", rotation=45)

        # Add overall title
        if end_date:
            title = f"Weather Conditions: {start_date} to {end_date}"
        else:
            title = f"Weather Conditions: {start_date}"
        fig1.suptitle(title, y=0.95)  # Adjust title position

        # Ensure proper spacing
        fig1.subplots_adjust(top=0.92, bottom=0.1, left=0.1, right=0.95, hspace=0.4)

        # Wind figures
        fig2, fig3 = create_wind_plots(combined_df, start_date, end_date)
        fig4 = create_3d_wind_plot(combined_df, start_date, end_date)

        # Save all plots to buffers
        weather_buf = io.BytesIO()
        wind_ts_buf = io.BytesIO()
        wind_rose_buf = io.BytesIO()
        wind_3d_buf = io.BytesIO()

        # Save to buffers with higher DPI
        fig1.savefig(weather_buf, format="png", bbox_inches="tight", dpi=300)
        fig2.savefig(wind_ts_buf, format="png", bbox_inches="tight", dpi=300)
        fig3.savefig(wind_rose_buf, format="png", bbox_inches="tight", dpi=300)
        fig4.savefig(wind_3d_buf, format="png", bbox_inches="tight", dpi=300)

        # Create filenames with consistent formatting
        if end_date:
            base_name = f"{start_date}_to_{end_date}"
        else:
            base_name = f"{start_date}"

        weather_filename = f"weather_plot_{base_name}.png"
        wind_ts_filename = f"wind_timeseries_{base_name}.png"
        wind_rose_filename = f"wind_rose_{base_name}.png"
        wind_3d_filename = f"wind_3d_{base_name}.png"

        # Only save locally if explicitly requested
        if save_locally:
            weather_filepath = Path(BOT_FIGURE_DIR) / weather_filename
            wind_ts_filepath = Path(BOT_FIGURE_DIR) / wind_ts_filename
            wind_rose_filepath = Path(BOT_FIGURE_DIR) / wind_rose_filename
            wind_3d_filepath = Path(BOT_FIGURE_DIR) / wind_3d_filename

            fig1.savefig(weather_filepath, format="png", bbox_inches="tight", dpi=300)
            fig2.savefig(wind_ts_filepath, format="png", bbox_inches="tight", dpi=300)
            fig3.savefig(wind_rose_filepath, format="png", bbox_inches="tight", dpi=300)
            fig4.savefig(wind_3d_filepath, format="png", bbox_inches="tight", dpi=300)
        else:
            # If not saving locally, just create Path objects but don't save
            weather_filepath = Path(BOT_FIGURE_DIR) / weather_filename
            wind_ts_filepath = Path(BOT_FIGURE_DIR) / wind_ts_filename
            wind_rose_filepath = Path(BOT_FIGURE_DIR) / wind_rose_filename
            wind_3d_filepath = Path(BOT_FIGURE_DIR) / wind_3d_filename

        weather_buf.seek(0)
        wind_ts_buf.seek(0)
        wind_rose_buf.seek(0)
        wind_3d_buf.seek(0)

        plt.close("all")

        return (
            (weather_filename, wind_ts_filename, wind_rose_filename, wind_3d_filename),
            (weather_buf, wind_ts_buf, wind_rose_buf, wind_3d_buf),
            (weather_filepath, wind_ts_filepath, wind_rose_filepath, wind_3d_filepath),
        )

    except Exception as e:
        raise Exception(f"Error creating plots: {str(e)}")
