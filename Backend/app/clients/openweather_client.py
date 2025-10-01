import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class OpenWeatherClient:
    GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
    ONECALL_URLS = [
        "https://api.openweathermap.org/data/3.0/onecall",
        "https://api.openweathermap.org/data/2.5/onecall",
    ]

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _geocode(self, city: str) -> Optional[Dict[str, float]]:
        r = requests.get(self.GEO_URL, params={"q": city, "limit": 1, "appid": self.api_key}, timeout=15)
        r.raise_for_status()
        js = r.json()
        if not js:
            return None
        first = js[0]
        return {"lat": first["lat"], "lon": first["lon"]}

    def _onecall_daily(self, lat: float, lon: float) -> Dict[str, Any]:
        params = {
            "lat": lat,
            "lon": lon,
            "exclude": "current,minutely,hourly,alerts",
            "units": "metric",
            "appid": self.api_key,
        }
        last_err = None
        for url in self.ONECALL_URLS:
            try:
                r = requests.get(url, params=params, timeout=20)
                if r.status_code in (401, 403):
                    logger.warning("OpenWeather unauthorized (%s) for %s — trying next fallback (if any)", r.status_code, url)
                    last_err = requests.HTTPError(f"{r.status_code} Unauthorized/Forbidden")
                    continue
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                logger.warning("OpenWeather request failed for %s: %s", url, e)
                last_err = e
                continue
        if last_err:
            logger.warning("OpenWeather failed completely, using only Open-Meteo data. Reason: %s", last_err)
        return {}

    def get_weather(self, city: str, days: int = 6) -> List[Dict[str, Any]]:
        loc = self._geocode(city)
        if not loc:
            return []

        data = self._onecall_daily(loc["lat"], loc["lon"])
        if not data or "daily" not in data:
            return []

        tz_offset = int(data.get("timezone_offset", 0))
        tz = timezone(timedelta(seconds=tz_offset))
        out: List[Dict[str, Any]] = []

        for d in (data.get("daily") or [])[:days]:
            dt_local = datetime.fromtimestamp(int(d["dt"]), tz=tz)
            out.append({
                "date": dt_local.date().isoformat(),
                "temperature": float(d.get("temp", {}).get("day", 0.0)),
                "humidity": float(d.get("humidity", 0.0)),
                "windspeed": float(d.get("wind_speed", 0.0)),
                "percipitation_probability": float(d.get("pop", 0.0)) * 100.0,
                "uv_index": int(round(float(d.get("uvi", 0.0)))),
                "cloudcover": float(d.get("clouds", 0.0)),
                "aod": None,
            })

        return out
