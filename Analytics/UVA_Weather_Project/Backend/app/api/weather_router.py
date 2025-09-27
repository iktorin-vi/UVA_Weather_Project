from fastapi import APIRouter, Depends
from app.clients.openweather_client import OpenWeatherClient
from app.services.weather_service import WeatherService
from app.models.weather_dto import WeatherDTO

router = APIRouter(prefix="/weather", tags=["Weather"])

async def get_weather_service() -> WeatherService:
    client = OpenWeatherClient()
    return WeatherService(client)

@router.get("/forecast", response_model=WeatherDTO)
async def get_weather(city: str, service: WeatherService = Depends(get_weather_service)):
    return await service.get_weather(city)
