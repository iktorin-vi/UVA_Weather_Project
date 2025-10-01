import requests
from typing import List, Dict, Any, Optional

class OpenMeteoClient:
    GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

    def _geocode(self, city: str) -> Optional[Dict[str, float]]:
        resp = requests.get(self.GEO_URL, params={"name": city, "count": 1, "language": "en", "format": "json"}, timeout=15)
        resp.raise_for_status()
        js = resp.json()
        if not js.get("results"):
            return None
        first = js["results"][0]
        return {"lat": first["latitude"], "lon": first["longitude"]}

    def _fetch_daily(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
            "wind_speed_unit": "ms",
            "forecast_days": days,
            "daily": ",".join([
                "temperature_2m_mean",
                "relative_humidity_2m_mean",
                "uv_index_max",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "cloud_cover_mean",
            ]),
        }
        r = requests.get(self.FORECAST_URL, params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    def _fetch_aod_hourly(self, lat: float, lon: float) -> Dict[str, Any]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
            "hourly": "aerosol_optical_depth",
        }
        r = requests.get(self.AIR_QUALITY_URL, params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    def get_weather(self, city: str, days: int = 6) -> List[Dict[str, Any]]:
        loc = self._geocode(city)
        if not loc:
            return []

        daily = self._fetch_daily(loc["lat"], loc["lon"], days)
        time_arr = daily.get("daily", {}).get("time", []) or []

        out: List[Dict[str, Any]] = []
        for i, ds in enumerate(time_arr[:days]):
            out.append({
                "date": ds,
                "temperature": float((daily["daily"].get("temperature_2m_mean") or [None])[i] or 0.0),
                "humidity": float((daily["daily"].get("relative_humidity_2m_mean") or [None])[i] or 0.0),
                "windspeed": float((daily["daily"].get("wind_speed_10m_max") or [None])[i] or 0.0),
                "percipitation_probability": float((daily["daily"].get("precipitation_probability_max") or [None])[i] or 0.0),
                "uv_index": int((daily["daily"].get("uv_index_max") or [0])[i] or 0),
                "cloudcover": float((daily["daily"].get("cloud_cover_mean") or [None])[i] or 0.0),
                "aod": 0.0,
            })

        try:
            aq = self._fetch_aod_hourly(loc["lat"], loc["lon"])
            t_hours = aq.get("hourly", {}).get("time", []) or []
            aod_hours = aq.get("hourly", {}).get("aerosol_optical_depth", []) or []
            buckets: Dict[str, List[float]] = {}
            for t_str, aod_val in zip(t_hours, aod_hours):
                d_str = t_str.split("T", 1)[0]
                buckets.setdefault(d_str, []).append(float(aod_val or 0.0))
            for item in out:
                day = item["date"]
                if day in buckets and buckets[day]:
                    item["aod"] = sum(buckets[day]) / len(buckets[day])
        except Exception:
            pass

        return out
