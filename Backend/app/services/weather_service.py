import os
import json
import datetime
import logging
from typing import List, Dict, Any

from app.models.weather_dto import WeatherDTO, ComfortDTO
from app.clients.openmeteo_client import OpenMeteoClient
from app.clients.openweather_client import OpenWeatherClient
from app.services.comfort_service import Sex, ComfortService

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self, openmeteo_client: OpenMeteoClient, openweather_client: OpenWeatherClient):
        self.openmeteo_client = openmeteo_client
        self.openweather_client = openweather_client
        self.file_path = "weather_forecast.json"

    def _ensure_cache(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            logger.info("Cache file not found, initializing new cache at %s", self.file_path)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    logger.warning("Cache file structure invalid, resetting cache")
                    return {}
                return data
        except json.JSONDecodeError:
            logger.warning("Cache file is corrupted JSON, resetting cache")
            return {}

    def _save_cache(self, data: Dict[str, Any]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.debug("Cache persisted to %s", self.file_path)

    @staticmethod
    def _six_dates_from_today() -> List[str]:
        today = datetime.date.today()
        return [(today + datetime.timedelta(days=i)).isoformat() for i in range(6)]

    @staticmethod
    def _sanitize_row(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "date": str(row.get("date") or ""),
            "humidity": float(row.get("humidity") or 0.0),
            "temperature": float(row.get("temperature") or 0.0),
            "windspeed": float(row.get("windspeed") or 0.0),
            "percipitation_probability": float(row.get("percipitation_probability") or 0.0),
            "uv_index": int(row.get("uv_index") or 0),
            "cloudcover": float(row.get("cloudcover") or 0.0),
            "aod": float(row.get("aod") or 0.0),
        }

    def get_weather(self, city: str) -> List[WeatherDTO]:
        city_key = city.lower()
        target_dates = self._six_dates_from_today()
        weather_data = self._ensure_cache()
        city_block: Dict[str, Any] = weather_data.get(city_key, {})
        missing = [d for d in target_dates if d not in city_block]
        if not missing:
            logger.info("Cache hit: city=%s, returning 6 days from cache", city)
            return [WeatherDTO(**self._sanitize_row(city_block[d])) for d in target_dates]

        logger.info("Cache miss: city=%s, missing_days=%s; fetching external forecasts", city, ",".join(missing))
        om_days = self.openmeteo_client.get_weather(city, days=6) or []
        logger.info("Open-Meteo returned %d daily rows for city=%s", len(om_days), city)
        try:
            ow_days = self.openweather_client.get_weather(city, days=6) or []
            logger.info("OpenWeather returned %d daily rows for city=%s", len(ow_days), city)
        except Exception as e:
            logger.warning("OpenWeather failed for city=%s: %s", city, e)
            ow_days = []

        by_date: Dict[str, Dict[str, Any]] = {}
        for row in om_days:
            d = str(row.get("date") or "")
            if d:
                by_date[d] = dict(row)
        for row in ow_days:
            d = str(row.get("date") or "")
            if not d:
                continue
            base = by_date.setdefault(d, {"date": d})
            for k, v in row.items():
                if k == "date":
                    continue
                if base.get(k) in (None, ""):
                    base[k] = v
        for d in target_dates:
            by_date.setdefault(d, {"date": d})

        weather_data.setdefault(city_key, {})
        created, skipped = 0, 0
        for d in target_dates:
            merged_row = self._sanitize_row(by_date.get(d, {"date": d}))
            if d not in weather_data[city_key] or not weather_data[city_key][d]:
                weather_data[city_key][d] = merged_row
                created += 1
            else:
                skipped += 1
        self._save_cache(weather_data)
        logger.info("Cache updated: city=%s, created=%d, kept=%d", city, created, skipped)

        return [WeatherDTO(**self._sanitize_row(weather_data[city_key][d])) for d in target_dates]

    def get_comfort(
        self,
        age: float,
        weight: float,
        height: float,
        sex: Sex,
        city: str,
        date: datetime.date
    ) -> ComfortDTO:
        city_key = city.lower()
        date_key = date.isoformat()
        weather_data = self._ensure_cache()
        city_block = weather_data.get(city_key)
        if not isinstance(city_block, dict) or date_key not in city_block:
            logger.error("Comfort lookup missed cache: city=%s date=%s; call /weather/forecast first", city, date_key)
            raise ValueError("No cached data for this city and date. Call /weather/forecast first.")
        logger.info("Computing comfort: city=%s date=%s", city, date_key)
        return ComfortService().get_comfort(
            weather_forecast=city_block[date_key],
            age=age,
            height=height,
            weight=weight,
            sex=sex
        )
