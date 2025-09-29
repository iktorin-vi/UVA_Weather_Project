from pydantic import BaseModel
from app.services.comfort_service import Sex

class WeatherDTO(BaseModel):
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
