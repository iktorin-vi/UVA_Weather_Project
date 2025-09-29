from enum import Enum
from services.comfort_service import ComfortDTO
import json

from enum import Enum
from services.comfort_service import ComfortDTO

class Sex(Enum):
    female = 0
    male = 1

class Metrics:
    def __init__(self, value: float, avg: float, std: float, coef: float):
        self.value = value
        self.avg = avg
        self.std = std
        self.coef = coef

    @property
    def normalized(self) -> float:
        return (self.value - self.avg) / self.std

class ComfortService:

    @staticmethod
    def calculation(intercept: float, temperature: Metrics, humidity: Metrics, wind_speed: Metrics,
                    uva: Metrics, aod: Metrics, sex: Metrics, age: Metrics,
                    height: Metrics, weight: Metrics, bmi: Metrics, formula_type: str) -> float:

        if formula_type == "temperature":
            return (
                intercept
                - 0.113674 * temperature.normalized
                + 0.006831 * humidity.normalized
                - 0.001155 * wind_speed.normalized
                + 0.002198 * uva.normalized
                + 0.010385 * aod.normalized
                - 0.002946 * sex.normalized
                - 0.028075 * age.normalized
                - 0.029417 * height.normalized
                + 0.051113 * weight.normalized
                - 0.064589 * bmi.normalized
            )
        elif formula_type == "humidity":
            return (
                intercept
                - 0.005279 * temperature.normalized
                - 0.097257 * humidity.normalized
                + 0.004332 * wind_speed.normalized
                + 0.001107 * uva.normalized
                - 0.002452 * aod.normalized
                + 0.000287 * sex.normalized
                - 0.000399 * age.normalized
                - 0.052156 * height.normalized
                + 0.097753 * weight.normalized
                - 0.127599 * bmi.normalized
            )
        elif formula_type == "uva":
            return (
                intercept
                + 0.000306 * temperature.normalized
                + 0.000452 * humidity.normalized
                - 0.000119 * wind_speed.normalized
                - 0.289377 * uva.normalized
                + 0.000268 * aod.normalized
                + 0.047674 * sex.normalized
                + 0.000190 * age.normalized
                + 0.000622 * height.normalized
                - 0.001603 * weight.normalized
                + 0.002149 * bmi.normalized
            )
        elif formula_type == "aod":
            return (
                intercept
                + 0.000438 * temperature.normalized
                - 0.000932 * humidity.normalized
                - 0.000755 * wind_speed.normalized
                - 0.000649 * uva.normalized
                - 0.266658 * aod.normalized
                - 0.037238 * age.normalized
                + 0.002514 * height.normalized
                - 0.004346 * weight.normalized
                + 0.005096 * bmi.normalized
            )
        elif formula_type == "wind":
            return (
                intercept
                - 0.000202 * temperature.normalized
                - 0.000983 * humidity.normalized
                - 0.239010 * wind_speed.normalized
                - 0.000655 * uva.normalized
                - 0.001607 * aod.normalized
                - 0.001358 * sex.normalized
                + 0.001223 * age.normalized
                - 0.004744 * height.normalized
                + 0.041076 * weight.normalized
                - 0.037158 * bmi.normalized
            )

    @staticmethod
    def get_comfort(weather_forecast: dict, age: float, height: float, weight: float, sex: Sex) -> ComfortDTO:

        # BMI
        height_m = height / 100
        BMI = weight / (height_m ** 2)

        # Metrics
        temperature = Metrics(weather_forecast["temperature"], 24.65, 8.47, -0.113674)
        humidity = Metrics(weather_forecast["humidity"], 54.65, 20.13, -0.097257)
        wind_speed = Metrics(weather_forecast["windspeed"], 7.48, 4.37, -0.239010)
        uva = Metrics(weather_forecast["uv_index"], 5.98, 3.52, -0.289377)
        aod = Metrics(weather_forecast["aod"], 0.54, 0.27, -0.266658)
        sex_metric = Metrics(sex.value, 0.51, 0.50, 0)
        age_metric = Metrics(age, 50.49, 19.06, 0)
        height_metric = Metrics(height, 170.02, 9.86, 0)
        weight_metric = Metrics(weight, 69.79, 15.10, 0)
        bmi_metric = Metrics(BMI, 24.38, 5.93, 0)


        comfort_temperature = ComfortService.calculation(
            0.648906, temperature, humidity, wind_speed, uva, aod,
            sex_metric, age_metric, height_metric, weight_metric, bmi_metric, "temperature"
        )
        comfort_humidity = ComfortService.calculation(
            0.636105, temperature, humidity, wind_speed, uva, aod,
            sex_metric, age_metric, height_metric, weight_metric, bmi_metric, "humidity"
        )
        comfort_UVA = ComfortService.calculation(
            0.455344, temperature, humidity, wind_speed, uva, aod,
            sex_metric, age_metric, height_metric, weight_metric, bmi_metric, "uva"
        )
        comfort_AOD = ComfortService.calculation(
            0.422675, temperature, humidity, wind_speed, uva, aod,
            sex_metric, age_metric, height_metric, weight_metric, bmi_metric, "aod"
        )
        comfort_wind = ComfortService.calculation(
            0.605284, temperature, humidity, wind_speed, uva, aod,
            sex_metric, age_metric, height_metric, weight_metric, bmi_metric, "wind"
        )

        # [0,1]
        comfort_values = {
            "temperature": min(max(comfort_temperature, 0), 1),
            "humidity": min(max(comfort_humidity, 0), 1),
            "wind_speed": min(max(comfort_wind, 0), 1),
            "uva": min(max(comfort_UVA, 0), 1),
            "aod": min(max(comfort_AOD, 0), 1)
        }

        simple_avg = sum(comfort_values.values()) / len(comfort_values)
        weights = {k: abs(v.coef) for k, v in zip(comfort_values.keys(), [temperature, humidity, wind_speed, uva, aod])}
        total_weight = sum(weights.values())
        weighted_avg = sum(comfort_values[k] * (weights[k]/total_weight) for k in comfort_values)

        return ComfortDTO(
            temperature=comfort_values["temperature"],
            humidity=comfort_values["humidity"],
            wind_speed=comfort_values["wind_speed"],
            uva=comfort_values["uva"],
            aod=comfort_values["aod"],
            simple_avg=simple_avg,
            weighted_avg=weighted_avg
        )
