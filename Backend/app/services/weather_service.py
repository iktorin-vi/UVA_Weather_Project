from app.models.weather_dto import WeatherDTO
from .comfort_service import ComfortService

class WeatherService:
    def __init__(self, weather_client):
        self.weather_client = weather_client

    async def get_weather(self, city: str) -> WeatherDTO:
        temperature=98
        humidity=8
        windspeed= 1
        percipitation_probability= 2
        uv_index= 3
        cloudcover= 4
        aod= 5

        return WeatherDTO(
            temperature=temperature,
            humidity=humidity,
            windspeed=windspeed,
            percipitation_probability=percipitation_probability,
            uv_index=uv_index,
            cloudcover=cloudcover,
            aod=aod
        )
