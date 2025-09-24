import json

from app.services.comfort_service import Sex
from app.models.weather_dto import WeatherDTO, ComfortDTO
from .comfort_service import ComfortService
from app.clients.openmeteo_client import OpenMeteoClient
from app.clients.openweather_client import OpenWeatherClient

class WeatherService:
    def __init__(self, 
                 openmeteo_client: OpenMeteoClient,
                  openweather_client: OpenWeatherClient ):
        self.openmeteo_client = openmeteo_client
        self.openweather_client = openweather_client

    async def get_weather(self, city: str) -> WeatherDTO:
        temperature=98
        humidity=8
        windspeed= 1
        percipitation_probability= 2
        uv_index= 3
        cloudcover= 4
        aod= 5

        # TODO: Save every json which will be constructed from openmeteo_client and openweather_client
        # TODO: Also check if this city will be forecased before take info from clients
        # TODO: If this data constained use its

        return WeatherDTO(
            temperature=temperature,
            humidity=humidity,
            windspeed=windspeed,
            percipitation_probability=percipitation_probability,
            uv_index=uv_index,
            cloudcover=cloudcover,
            aod=aod
        )
    
    # TODO: Add any additional params that are needed
    async def get_comfort(age: float, weight: float, height: float, sex: Sex) -> ComfortDTO:
        # TODO: Get local stored json which will be saved when get_weather function will be used 
        weather_forecast_data = json()

        ComfortService().get_comfort(weather_forecast_data)

        return ComfortDTO()
