from pydantic import BaseModel
from typing import Dict, Optional

class WeatherDTO(BaseModel):
    date: Optional[str] = None
    humidity: float
    temperature: float
    windspeed: float
    percipitation_probability: float
    uv_index: int
    cloudcover: float
    aod: float

class ComfortDTO(BaseModel):
    temperature: float
    humidity: float
    wind_speed: float
    uva: float
    aod: float
    simple_avg: float = 0.0
    weighted_avg: float = 0.0
    advice: Dict[str, str] = {}
