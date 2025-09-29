# UVA_Weather_Project
NASA Space App Challenge Hackathon Project

# Backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload --app-dir app

# Analytics
### The main goal of this project is to create a personalized comfort index model that calculates an individual's comfort level based on both external meteorological parameters (temperature, wind speed, humidity, UVA, AOD) and personal anthropometric data (age, gender, BMI derived from height and weight).
The analysis was successfully completed using a regression model with the following outcomes:
-  Dependencies Identified: External and personal factors influencing the comfort index were quantified.
-  BMI Incorporated: Height and weight were used to calculate Body Mass Index as a key feature.
-  Coefficients Extracted: Model coefficients were obtained to measure each factor’s impact.
-  JSON Configuration Created: All parameters were structured into a JSON file.
### Installation
#### Create virtual environment (recommended)
python -m venv comfort_env
comfort_env\Scripts\activate 
#### Install dependencies
pip install -r requirements.txt
