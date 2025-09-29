# Documentation: Comfort Calculation Based on Meteorological and Anthropometric Parameters

## Overview

This document contains formulas for calculating comfort indices based on meteorological conditions and individual human characteristics.  
The system uses input parameter normalization and linear models to predict comfort levels.

**Data source:**  
The coefficients were obtained from a JSON file generated through data analysis and linear model training.  
The model was trained on a synthetic dataset with additional inputs collected from surveyed individuals.

---

## Input Parameter Normalization

Normalization formula: parameter_norm = (parameter - mean_value) / standard_deviation

### Normalization values

| Parameter      | Mean   | Standard Deviation |
|----------------|--------|--------------------|
| **temperature** | 24.65 | 8.47  |
| **humidity**    | 54.65 | 20.13 |
| **wind_speed**  | 7.48  | 4.37  |
| **UVA**         | 5.98  | 3.52  |
| **AOD**         | 0.54  | 0.27  |
| **sex**         | 0.51  | 0.50  |
| **age**         | 50.49 | 19.06 |
| **height**      | 170.02| 9.86  |
| **weight**      | 69.79 | 15.10 |
| **BMI**         | 24.38 | 5.93  |

>  `sex` is encoded as `0` (female) or `1` (male).

##  General Formula for Comfort Parameters
comfort_X = β₀ + β₁×temperature_norm + β₂×humidity_norm + β₃×wind_speed_norm
+ β₄×UVA_norm + β₅×AOD_norm + β₆×sex_norm + β₇×age_norm
+ β₈×height_norm + β₉×weight_norm + β₁₀×BMI_norm
  
- `β₀` — intercept  
- `β₁-β₁₀` — coefficients for normalized parameters  
- `comfort_X` — comfort index in the range [0, 1]

---

## Specific Formulas

### 1. Comfort by Temperature
comfort_temperature = 0.648906 - 0.113674×temperature_norm + 0.006831×humidity_norm
- 0.001155×wind_speed_norm + 0.002198×UVA_norm
+ 0.010385×AOD_norm - 0.002946×sex_norm - 0.028075×age_norm
- 0.029417×height_norm + 0.051113×weight_norm
- 0.064589×BMI_norm
### 2. Comfort by Humidity
comfort_humidity = 0.636105 - 0.005279×temperature_norm - 0.097257×humidity_norm
+ 0.004332×wind_speed_norm + 0.001107×UVA_norm
- 0.002452×AOD_norm + 0.000287×sex_norm - 0.000399×age_norm
- 0.052156×height_norm + 0.097753×weight_norm
- 0.127599×BMI_norm
### 3. Comfort by UVA Radiation
comfort_UVA = 0.455344 + 0.000306×temperature_norm + 0.000452×humidity_norm
- 0.000119×wind_speed_norm - 0.289377×UVA_norm + 0.000268×AOD_norm
+ 0.047674×sex_norm + 0.000190×age_norm + 0.000622×height_norm
- 0.001603×weight_norm + 0.002149×BMI_norm

### 4. Comfort by Aerosol Optical Depth (AOD)
comfort_AOD = 0.422675 + 0.000438×temperature_norm - 0.000932×humidity_norm
- 0.000755×wind_speed_norm - 0.000649×UVA_norm - 0.266658×AOD_norm
- 0.037238×age_norm + 0.002514×height_norm - 0.004346×weight_norm
+ 0.005096×BMI_norm
### 5. Comfort by Wind Speed
comfort_wind = 0.605284 - 0.000202×temperature_norm - 0.000983×humidity_norm
- 0.239010×wind_speed_norm - 0.000655×UVA_norm - 0.001607×AOD_norm
- 0.001358×sex_norm + 0.001223×age_norm - 0.004744×height_norm
+ 0.041076×weight_norm - 0.037158×BMI_norm


---

## Example Calculation

**Input data:**
- temperature = 25.0  
- humidity = 60.0  
- wind_speed = 5.0  
- UVA = 3.0  
- AOD = 0.3  
- sex = 1  
- age = 35  
- height = 175  
- weight = 70  
- BMI = 22.86  

**Results:**
- comfort_temperature = `0.6578` (65.8%)  
- comfort_humidity = `0.6172` (61.7%)  
- comfort_wind = `0.7482` (74.8%)  
- comfort_UVA = `0.7465` (74.6%)  
- comfort_AOD = `0.6945` (69.4%)  

---

## Backend Development Instructions

1. **Calculate BMI**
   BMI = weight / (height/100 * height/100)  # weight in kg, height in cm
2. Normalize Parameters
Use the mean and standard deviation values from the normalization table:
parameter_norm = (parameter - mean_value) / standard_deviation
3. Substitute into Comfort Formulas
Compute each comfort_parameter using the provided formulas.
4. Interpret Results
Values are in the range [0, 1]
Multiply by 100 to convert into percentages
Higher values = higher comfort level


### Overall Comfort Calculation
#### Method 1: Simple Averaging
overall_comfort = (comfort_temperature + comfort_humidity + comfort_wind 
                  + comfort_UVA + comfort_AOD) / 5

#### Method 2: Weighted Averaging (recommended)

Step 1: Determine weights
Take the absolute values of key coefficients:

w_temp = | -0.113674 |

w_hum = | -0.097257 |

w_wind = | -0.239010 |

w_uva = | -0.289377 |

w_aod = | -0.266658 |

Step 2: Normalize weights

total_weight = w_temp + w_hum + w_wind + w_uva + w_aod
weight_temp = w_temp / total_weight
weight_hum = w_hum / total_weight
weight_wind = w_wind / total_weight
weight_uva = w_uva / total_weight
weight_aod = w_aod / total_weight

Step 3: Calculate overall comfort

overall_comfort = (weight_temp * comfort_temperature + 
                   weight_hum * comfort_humidity + 
                   weight_wind * comfort_wind + 
                   weight_uva * comfort_UVA + 
                   weight_aod * comfort_AOD)
The weighted method accounts for parameter importance.

Notes
- Coefficients (β) were obtained from a JSON file after model training

- The model was trained on both synthetic and real survey data

- Comfort values are probabilities or satisfaction levels (0 = minimum comfort, 1 = maximum comfort)

- Convert to percentages by multiplying by 100

- The system accounts for both environmental conditions and individual characteristics

