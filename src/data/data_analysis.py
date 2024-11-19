import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Read the CSV file
def load_weather_data(file_path):
    df = pd.read_csv(file_path)
    # Convert timestamp to datetime
    df['tNow'] = pd.to_datetime(df['tNow'])
    return df

def analyze_wind_patterns(df):
    # Calculate basic statistics for wind components
    wind_stats = {
        'Wind Speed (2D)': df['2dSpeed_m_s'].describe(),
        'Wind Speed (3D)': df['3DSpeed_m_s'].describe(),
        'Wind Direction': df['Azimuth_deg'].describe(),
        'Vertical Wind': df['w_m_s'].describe()
    }
    
    # Calculate wind gustiness (standard deviation of wind speed)
    wind_gustiness = df['3DSpeed_m_s'].rolling(window=10).std()
    
    # Calculate wind variability
    wind_direction_variability = df['Azimuth_deg'].rolling(window=10).std()
    
    return wind_stats, wind_gustiness, wind_direction_variability

def analyze_atmospheric_conditions(df):
    # Calculate correlations between parameters
    atmos_params = ['Press_Pa', 'Temp_C', 'Hum_RH', '3DSpeed_m_s']
    correlation_matrix = df[atmos_params].corr()
    
    # Look for rapid pressure changes (potential hurricane indicator)
    pressure_change = df['Press_Pa'].diff()
    
    return correlation_matrix, pressure_change

def main():
    # Load the data
    df = load_weather_data('src/data/merged_weather_data.csv')
    
    # Analyze wind patterns
    wind_stats, wind_gustiness, wind_direction_var = analyze_wind_patterns(df)
    
    # Analyze atmospheric conditions
    corr_matrix, pressure_change = analyze_atmospheric_conditions(df)
    
    # Print initial findings
    print("\nWind Statistics:")
    print(wind_stats)
    
    print("\nCorrelation Matrix:")
    print(corr_matrix)
    
    # Create basic visualizations
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Wind speed and direction
    axes[0,0].scatter(df['u_m_s'], df['v_m_s'], alpha=0.5)
    axes[0,0].set_title('Wind Components (u vs v)')
    axes[0,0].set_xlabel('u (m/s)')
    axes[0,0].set_ylabel('v (m/s)')
    
    # Time series of 3D wind speed
    axes[0,1].plot(df['tNow'], df['3DSpeed_m_s'])
    axes[0,1].set_title('3D Wind Speed Over Time')
    axes[0,1].set_xlabel('Time')
    axes[0,1].set_ylabel('Wind Speed (m/s)')
    
    # Pressure over time
    axes[1,0].plot(df['tNow'], df['Press_Pa'])
    axes[1,0].set_title('Pressure Over Time')
    axes[1,0].set_xlabel('Time')
    axes[1,0].set_ylabel('Pressure (Pa)')
    
    # Temperature and humidity
    axes[1,1].scatter(df['Temp_C'], df['Hum_RH'], alpha=0.5)
    axes[1,1].set_title('Temperature vs Humidity')
    axes[1,1].set_xlabel('Temperature (°C)')
    axes[1,1].set_ylabel('Relative Humidity (%)')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()