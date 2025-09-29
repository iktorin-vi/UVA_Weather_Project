from enum import Enum
from services.comfort_service import ComfortDTO  
import json
from pathlib import Path

COEFFICIENTS_FILE = Path("UVA_Weather_Project/services/coefficient.json")
with open(COEFFICIENTS_FILE, "r") as file:
    COEFFICIENTS = json.load(file)


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
        if self.std == 0:
            return 0
        return (self.value - self.avg) / self.std


class ComfortService:

    @staticmethod
    def calculation(metrics: dict, formula_name: str) -> float:
        formula = COEFFICIENTS["formulas"][formula_name]
        result = formula["intercept"]
        for key, metric in metrics.items():
            coef = formula["coefficients"].get(key, 0)
            result += coef * metric.normalized
        return result

    @staticmethod
    def get_comfort(weather_forecast: dict, age: float, height: float, weight: float, sex: Sex) -> ComfortDTO:

        # BMI
        height_m = height / 100
        BMI = weight / (height_m ** 2)

        # Metrics 
        reference_formula = "comfort_temperature"
        scaling = COEFFICIENTS["formulas"][reference_formula]["scaling_params"]
        coefficients = COEFFICIENTS["formulas"][reference_formula]["coefficients"]

        # Створюємо словник метрик
        metrics = {
            "temperature": Metrics(weather_forecast["temperature"], scaling["temperature"]["mean"], scaling["temperature"]["std"], coefficients["temperature"]),
            "humidity": Metrics(weather_forecast["humidity"], scaling["humidity"]["mean"], scaling["humidity"]["std"], coefficients["humidity"]),
            "wind_speed": Metrics(weather_forecast["windspeed"], scaling["wind_speed"]["mean"], scaling["wind_speed"]["std"], coefficients["wind_speed"]),
            "UVA": Metrics(weather_forecast["uv_index"], scaling["UVA"]["mean"], scaling["UVA"]["std"], coefficients["UVA"]),
            "AOD": Metrics(weather_forecast["aod"], scaling["AOD"]["mean"], scaling["AOD"]["std"], coefficients["AOD"]),
            "sex": Metrics(sex.value, scaling["sex"]["mean"], scaling["sex"]["std"], coefficients["sex"]),
            "age": Metrics(age, scaling["age"]["mean"], scaling["age"]["std"], coefficients["age"]),
            "height": Metrics(height, scaling["height"]["mean"], scaling["height"]["std"], coefficients["height"]),
            "weight": Metrics(weight, scaling["weight"]["mean"], scaling["weight"]["std"], coefficients["weight"]),
            "BMI": Metrics(BMI, scaling["BMI"]["mean"], scaling["BMI"]["std"], coefficients["BMI"])
        }

        comfort_values = {
            "temperature": min(max(ComfortService.calculation(metrics, "comfort_temperature"), 0), 1),
            "humidity": min(max(ComfortService.calculation(metrics, "comfort_humidity"), 0), 1),
            "wind_speed": min(max(ComfortService.calculation(metrics, "comfort_wind"), 0), 1),
            "uva": min(max(ComfortService.calculation(metrics, "comfort_UVA"), 0), 1),
            "aod": min(max(ComfortService.calculation(metrics, "comfort_AOD"), 0), 1)
        }

        simple_avg = sum(comfort_values.values()) / len(comfort_values)
        weights = {k: abs(v.coef) for k, v in metrics.items() if k in comfort_values}
        total_weight = sum(weights.values())
        weighted_avg = sum(comfort_values[k] * (weights[k] / total_weight) for k in comfort_values)

        return ComfortDTO(
            temperature=comfort_values["temperature"],
            humidity=comfort_values["humidity"],
            wind_speed=comfort_values["wind_speed"],
            uva=comfort_values["uva"],
            aod=comfort_values["aod"],
            simple_avg=simple_avg,
            weighted_avg=weighted_avg
        )

