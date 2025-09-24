from enum import Enum, IntEnum, auto
import json

class Sex(Enum):
    male = 0,
    female = 1,

class ComfortService:
    def get_comfort(weather_forecast: json, age: float, height: float, weight: float, sex: Sex) -> json:
        pass