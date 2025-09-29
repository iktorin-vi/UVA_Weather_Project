from enum import Enum
from services.comfort_service import ComfortDTO
import json

class Sex(Enum):
    female = 0,
    male = 1,

class Metrics:
    coefficient: float
    normalize: float

class ComfortService:
    def get_comfort(weather_forecast: json, age: float, height: float, weight: float, sex: Sex) -> ComfortDTO:
        pass

    def get_normalize(metric: float, avg_metric: float, std_metric: float) -> float:
        pass

    def calculation(intercept: float, temperature: Metrics, humidity: Metrics, wind_speed: Metrics, uva: Metrics,
                    aod: Metrics, sex: Metrics, age: Metrics, height: Metrics, weight: Metrics, bmi: Metrics) -> float:
        pass