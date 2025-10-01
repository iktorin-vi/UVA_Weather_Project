import os
import logging
from typing import Optional, List
import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from app.clients.openweather_client import OpenWeatherClient
from app.clients.openmeteo_client import OpenMeteoClient
from app.services.weather_service import WeatherService
from app.models.weather_dto import WeatherDTO, ComfortDTO
from app.services.comfort_service import Sex

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["Weather"])

def get_weather_service() -> WeatherService:
    om_client = OpenMeteoClient()
    ow_client = OpenWeatherClient(api_key=OPENWEATHER_API_KEY)
    return WeatherService(om_client, ow_client)

def _parse_sex(value: str) -> Sex:
    v = str(value).strip().lower()
    if v in ("male", "1", "m"):
        return Sex.male
    if v in ("female", "0", "f"):
        return Sex.female
    raise ValueError(f"Unsupported sex value: {value}")

@router.get("/forecast", response_model=List[WeatherDTO])
def get_weather(city: str, service: WeatherService = Depends(get_weather_service)):
    logger.info("Fetching 6-day forecast: city=%s", city)
    return service.get_weather(city)

@router.get("/comfort", response_model=ComfortDTO)
def get_comfort(age: float,
                weight: float,
                height: float,
                sex: str,
                city: str,
                ts: Optional[int] = None,
                service: WeatherService = Depends(get_weather_service)):
    try:
        sex_enum = _parse_sex(sex)
    except ValueError as e:
        logger.error("Invalid sex parameter: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query param 'sex' must be one of: male, female, 1, 0, m, f"
        )
    if ts:
        if ts > 10**12:
            ts //= 1000
        date = datetime.date.fromtimestamp(ts)
    else:
        date = datetime.date.today()
    logger.info("Computing comfort: city=%s date=%s age=%s height=%s weight=%s sex=%s",
                city, date.isoformat(), age, height, weight, sex_enum.name)
    return service.get_comfort(age, weight, height, sex_enum, city, date)
