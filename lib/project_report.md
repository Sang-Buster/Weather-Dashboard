<div align="center">
<h1>Hurricane Milton Weather Analysis: Statistical Analysis and Machine Learning Approaches</h1>
<h6 align="center"><small>Sarah E. Reed, Xu Xiong, Sang Xing</small></h6>
</div>

## Abstract
This study presents a comprehensive analysis of weather patterns during Hurricane Milton using high-frequency (1Hz) data collected from a custom Raspberry Pi weather station. We employed various statistical and machine learning approaches to analyze wind behavior and environmental conditions, including exploratory data analysis, principal component analysis, and predictive modeling. Our findings reveal significant correlations between wind patterns and other environmental parameters, with machine learning models achieving up to 96.2% accuracy in predicting high-wind events.

## 1. Introduction
Hurricane Milton provided a unique opportunity to study local weather patterns during extreme weather events. Using a custom-built weather station, we collected high-frequency data to analyze the relationships between various environmental parameters and wind behavior. This analysis aims to:
- Identify key patterns in wind behavior during the hurricane
- Understand correlations between environmental parameters
- Develop predictive models for high-wind events
- Provide insights for future weather monitoring and prediction

## 2. Data Collection and Methodology

### 2.1 Data Collection
Data was collected using a Raspberry Pi-based weather station located at 60ft elevation, measuring:
- Wind components (u, v, w) in m/s
- 2D and 3D wind speeds
- Wind direction (azimuth and elevation)
- Atmospheric pressure
- Temperature (air and sonic)
- Relative humidity

### 2.2 Analysis Methods
Our analysis comprised three main approaches:
1. **Exploratory Data Analysis (EDA)**
   - Correlation analysis
   - Descriptive statistics
   - Wind direction quadrant analysis
   
2. **Principal Component Analysis (PCA)**
   - Dimension reduction
   - Feature importance analysis
   - Temporal pattern identification

3. **Machine Learning Models**
   - Logistic Regression
   - Decision Tree
   - Random Forest

## 3. Results and Discussion

### 3.1 Exploratory Data Analysis

#### 3.1.1 Correlation Analysis
Key correlations discovered:
- Strong negative correlation between temperature and humidity (-0.706)
- Moderate negative correlation between 3D wind speed and pressure (-0.395)
- Weak correlation between wind direction and other parameters

#### 3.1.2 Wind Direction Analysis
Wind patterns by quadrant showed distinct characteristics:
- North-East (N-E): 139,297 observations, mean speed 4.87 m/s
- East-South (E-S): 31,993 observations, mean speed 4.28 m/s
- South-West (S-W): 9,298 observations, mean speed 5.85 m/s
- West-North (W-N): 45,356 observations, mean speed 6.32 m/s

#### 3.1.3 Extreme Value Analysis
- 99th percentile wind speed: 15.32 m/s
- Maximum vertical wind: 9.20 m/s
- Maximum gust factor: 5.003

### 3.2 Principal Component Analysis

#### 3.2.1 Variance Explanation
The first six principal components explain 90.90% of total variance:
- PC1: 30.85%
- PC2: 17.63%
- PC3: 15.66%
- PC4: 12.87%
- PC5: 8.80%
- PC6: 5.09%

#### 3.2.2 Component Interpretation
Top contributing features for primary components:
- PC1: Temperature-related (SonicTemp_C, Temp_C)
- PC2: Wind-related (u_m_s, Elev_deg)
- PC3: Humidity and elevation angles
- PC4: Pressure and velocity components
- PC5: Temporal patterns (hour)

### 3.3 Machine Learning Models

#### 3.3.1 Model Performance
Using a wind speed threshold of 15.6 m/s (tropical depression strength):

**Logistic Regression:**
- Accuracy: 93.67%
- ROC-AUC: 0.984 ± 0.002
- Positive predictions: 7.18%

**Decision Tree:**
- Accuracy: 98.99%
- ROC-AUC: 0.684 ± 0.014
- Positive predictions: 0.83%

**Random Forest:**
- Accuracy: 99.25%
- ROC-AUC: 0.966 ± 0.008
- Positive predictions: 0.77%

#### 3.3.2 Feature Importance
Random Forest temporal importance analysis revealed:
1. 2D wind speed (t-9): 0.963
2. v-component (t-9): 0.002
3. w-component (t-9): 0.002

## 4. Conclusions
Our analysis revealed several key findings:
1. Wind patterns showed strong directional preferences, with highest speeds in the W-N quadrant
2. Temperature and humidity demonstrated strong inverse relationships
3. PCA identified distinct patterns in temperature and wind components
4. Random Forest achieved the best performance in predicting high-wind events
5. Historical wind speeds (t-9) were the most important predictive features

## 5. Future Work
Future research directions include:
- Integration of additional environmental sensors
- Development of real-time prediction capabilities
- Extension of the analysis to other weather events
- Implementation of more advanced machine learning techniques

## References
[Include relevant references]

## Acknowledgments
We thank Kaleb Nails, Marc Compere, and Avinash Muthu Krishnan for their contributions to the hardware setup and data collection system.