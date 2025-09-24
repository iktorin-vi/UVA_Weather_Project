from pydantic import BaseModel

class WeatherDTO(BaseModel):
    humidity: float
    temperature: float
    windspeed: float
    percipitation_probability: float
    uv_index: int
    cloudcover: float
    aod: float
