<div align="center">
<h1>Hurricane Milton Weather Analysis</h1>
<h6 align="center"><small>Sarah E. Reed, Xu Xiong, Sang Xing</small></h6>
</div>

## Project Overview
We propose to develop a comprehensive weather analysis dashboard focused on Hurricane Milton, leveraging real-time weather data collected at 1Hz frequency from a custom Raspberry Pi weather station. The project aims to visualize and analyze weather patterns, with particular emphasis on wind behavior during Hurricane Milton (October 8-10, 2024).

## Objectives
1. Create an interactive web dashboard for real-time weather data visualization
2. Analyze wind patterns and environmental conditions during Hurricane Milton
3. Apply statistical and machine learning methods to identify key factors contributing to hurricane behavior
4. Provide open-source access to both the data and analysis tools

## Data Collection
- **Hardware**: Raspberry Pi-based weather station
- **Location**: 60ft elevation on a light pole at [location](https://maps.app.goo.gl/noC7dszEV9brfdxy8)
- **Frequency**: 1 Hz (continuous)
- **Measurements**:
  - Wind components (u, v, w) in m/s
  - 2D and 3D wind speeds
  - Wind direction (azimuth and elevation)
  - Atmospheric pressure
  - Temperature (air and sonic)
  - Relative humidity
  - Error detection values

## Technical Implementation

### Dashboard Components
1. **Wind Rose Diagram**
   - Displays wind direction and speed distribution
   - Interactive selection of time periods
   - Customizable speed and direction bins

2. **Time Series Analysis**
   - Environmental parameters visualization
   - Wind speed and direction over time
   - Customizable time intervals and parameters

3. **Data Processing Pipeline**
   - Real-time data ingestion
   - Statistical preprocessing
   - MongoDB integration for data storage

### Statistical Analysis Plan
1. **Exploratory Data Analysis**
   - Basic statistical measures
   - Time series decomposition
   - Correlation analysis between variables

2. **Machine Learning Approaches**
   - Time series forecasting models
   - Pattern recognition in wind behavior
   - Anomaly detection during hurricane conditions

## Technology Stack
- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: MongoDB
- **Deployment**: Streamlit Cloud
- **Version Control**: GitHub

## Expected Outcomes
1. A live, interactive dashboard accessible at [https://hurricane-milton.streamlit.app/](https://hurricane-milton.streamlit.app/)
2. Statistical models explaining Hurricane Milton's behavior
3. Open-source codebase for community contribution
4. Research findings on hurricane wind patterns

## Timeline

### Phase 1 (Completed: Prior to Nov 18)
- Basic dashboard implementation
- Data collection infrastructure
- Initial exploratory analysis

### Phase 2 (Nov 18-22)
- **Monday, Nov 18**
  - Advanced statistical analysis implementation
  - Begin machine learning model development
  
- **Tuesday, Nov 19**
  - Continue model development
  - Start pattern recognition implementation
  - Begin drafting project report introduction and methods sections

- **Wednesday, Nov 20**
  - Model testing and validation
  - Begin presentation slide creation
  - Continue project report writing (results section)

- **Thursday, Nov 21**
  - Finalize initial models
  - Complete first draft of presentation slides
  - Continue project report writing (discussion section)

- **Friday, Nov 22**
  - Model refinement based on initial results
  - Internal team presentation review
  - Project report peer review

### Phase 3 (Nov 25-26)
- **Monday, Nov 25**
  - Final model optimization
  - Finalize presentation slides
  - Complete project report draft
  - Team rehearsal for presentation

- **Tuesday, Nov 26**
  - Final presentation delivery
  - Submit final project report
  - Code repository documentation update
  - Project submission

## Resources
- **Code Repository**: [https://github.com/Sang-Buster/weather-dashboard](https://github.com/Sang-Buster/weather-dashboard)
- **Data Storage**: MongoDB time series database
- **Computing Resources**: Cloud-based deployment
- **Team Members**: 
  - Sarah R.Reed (Software Author)
  - Xu Xiong (Software Author)
  - Sang Xing (Software & Hardware set-up Author)
  - Kaleb Nails (Hardware set-up Contributor)
  - Marc Compere (Hardware set-up Contributor)
  - Avinash Muthu Krishnan (Hardware set-up Contributor)

## Impact
This project will contribute to:
1. Understanding hurricane behavior live data analysis
2. Open-source weather monitoring solutions
3. Real-time environmental data visualization
4. Community-driven weather research

## Success Metrics
1. Dashboard uptime and performance
2. Model accuracy in explaining hurricane patterns
3. Community engagement and contributions
4. Research findings quality and relevance

This proposal aligns with modern data science practices while maintaining focus on practical weather monitoring and analysis applications.