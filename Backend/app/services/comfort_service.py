from enum import Enum
from pathlib import Path
import json
from typing import Dict

from app.models.weather_dto import ComfortDTO

BASE_DIR = Path(__file__).resolve().parent
COEFFICIENTS_FILE = BASE_DIR / "coefficient.json"
ADVICE_RULES_FILE = BASE_DIR / "advice_rules.json"

def _load_json(path: Path, default: dict) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

COEFFICIENTS = _load_json(COEFFICIENTS_FILE, {"formulas": {}})

DEFAULT_ADVICE_RULES = {
    "aod": [
        {"operator": ">", "value": 0.5,
         "text": "Рекомендується обмежити прогулянки на вулиці, особливо людям із проблемами дихальної системи. Використовуйте захисні маски."}
    ],
    "uv": [
        {"operator": ">", "value": 6,
         "text": "Слід уникати прямого сонячного випромінювання. Використовуйте сонцезахисний крем та носіть головні убори. Людям зі шкірними проблемами бажано залишатися вдома."}
    ],
    "humidity": [
        {"operator": ">", "value": 80,
         "text": "Фізичні навантаження варто зменшити. Людям із серцево-судинними проблемами рекомендується перебувати у прохолодних приміщеннях."}
    ],
    "wind": [
        {"operator": ">", "value": 10,
         "text": "Особи з алергіями повинні обмежити перебування надворі, оскільки вітер підвищує концентрацію пилку та пилу."}
    ],
    "temperature": [
        {"operator": "<", "value": 0,
         "text": "Тепло одягайтеся, людям із проблемами кровообігу варто уникати довгих прогулянок."},
        {"operator": ">", "value": 30,
         "text": "Уникайте перегріву, пийте достатньо води, людям із серцевими проблемами краще залишатися вдома у прохолоді."}
    ]
}
ADVICE_RULES = _load_json(ADVICE_RULES_FILE, DEFAULT_ADVICE_RULES)

class Sex(Enum):
    female = 0
    male = 1

class Metrics:
    def __init__(self, value: float, avg: float, std: float, coef: float):
        self.value = value
        self.avg = avg
        self.std = std
        self.coef = coef

    @property
    def normalized(self) -> float:
        if not self.std:
            return 0.0
        return (self.value - self.avg) / self.std

class ComfortService:
    @staticmethod
    def calculation(metrics: dict, formula_name: str) -> float:
        if formula_name not in COEFFICIENTS.get("formulas", {}):
            return 0.0
        formula = COEFFICIENTS["formulas"][formula_name]
        result = float(formula.get("intercept", 0.0))
        for key, metric in metrics.items():
            coef = float(formula.get("coefficients", {}).get(key, 0.0))
            result += coef * metric.normalized
        return result

    @staticmethod
    def _advices_from_rules(weather_forecast: dict) -> Dict[str, str]:
        adv: Dict[str, str] = {}

        aod = float(weather_forecast.get("aod", 0.0))
        uv = float(weather_forecast.get("uv_index", 0.0))
        humidity = float(weather_forecast.get("humidity", 0.0))
        wind_ms = float(weather_forecast.get("windspeed", 0.0))
        wind_kmh = wind_ms * 3.6
        temperature = float(weather_forecast.get("temperature", 0.0))

        def apply(metric_key: str, value: float):
            rules = ADVICE_RULES.get(metric_key, [])
            for r in rules:
                op = r.get("operator") or r.get("operatior")
                threshold = float(r.get("value", 0.0))
                text = str(r.get("text", ""))
                ok = False
                if op == ">":
                    ok = value > threshold
                elif op == "<":
                    ok = value < threshold
                elif op == ">=":
                    ok = value >= threshold
                elif op == "<=":
                    ok = value <= threshold
                elif op == "==":
                    ok = value == threshold
                if ok and text:
                    adv[metric_key] = text
                    break

        apply("aod", aod)
        apply("uv", uv)
        apply("humidity", humidity)
        apply("wind", wind_kmh)
        apply("temperature", temperature)

        return adv

    @staticmethod
    def get_comfort(weather_forecast: dict, age: float, height: float, weight: float, sex: Sex) -> ComfortDTO:
        height_m = height / 100.0 if height else 0.0
        BMI = (weight / (height_m ** 2)) if height_m else 0.0

        reference_formula = "comfort_temperature"
        scaling = COEFFICIENTS.get("formulas", {}).get(reference_formula, {}).get("scaling_params", {})
        coefficients = COEFFICIENTS.get("formulas", {}).get(reference_formula, {}).get("coefficients", {})

        def S(k, default_mean=0.0, default_std=1.0):
            s = scaling.get(k, {})
            return float(s.get("mean", default_mean)), float(s.get("std", default_std))

        def C(k):
            return float(coefficients.get(k, 0.0))

        metrics = {
            "temperature": Metrics(float(weather_forecast.get("temperature", 0.0)), *S("temperature"), C("temperature")),
            "humidity":    Metrics(float(weather_forecast.get("humidity", 0.0)),    *S("humidity"),    C("humidity")),
            "wind_speed":  Metrics(float(weather_forecast.get("windspeed", 0.0)),   *S("wind_speed"),  C("wind_speed")),
            "UVA":         Metrics(float(weather_forecast.get("uv_index", 0.0)),    *S("UVA"),         C("UVA")),
            "AOD":         Metrics(float(weather_forecast.get("aod", 0.0)),         *S("AOD"),         C("AOD")),
            "sex":         Metrics(float(sex.value),                                 *S("sex"),         C("sex")),
            "age":         Metrics(float(age),                                       *S("age"),         C("age")),
            "height":      Metrics(float(height),                                    *S("height"),      C("height")),
            "weight":      Metrics(float(weight),                                    *S("weight"),      C("weight")),
            "BMI":         Metrics(float(BMI),                                       *S("BMI"),         C("BMI")),
        }

        comfort_values = {
            "temperature": max(0.0, min(1.0, ComfortService.calculation(metrics, "comfort_temperature"))),
            "humidity":    max(0.0, min(1.0, ComfortService.calculation(metrics, "comfort_humidity"))),
            "wind_speed":  max(0.0, min(1.0, ComfortService.calculation(metrics, "comfort_wind"))),
            "uva":         max(0.0, min(1.0, ComfortService.calculation(metrics, "comfort_UVA"))),
            "aod":         max(0.0, min(1.0, ComfortService.calculation(metrics, "comfort_AOD"))),
        }

        simple_avg = sum(comfort_values.values()) / len(comfort_values)

        weight_keys = ["temperature", "humidity", "wind_speed", "UVA", "AOD"]
        total_w = sum(abs(metrics[k].coef) for k in weight_keys) or 1.0
        weighted_avg = (
            comfort_values["temperature"] * abs(metrics["temperature"].coef) +
            comfort_values["humidity"]    * abs(metrics["humidity"].coef) +
            comfort_values["wind_speed"]  * abs(metrics["wind_speed"].coef) +
            comfort_values["uva"]         * abs(metrics["UVA"].coef) +
            comfort_values["aod"]         * abs(metrics["AOD"].coef)
        ) / total_w

        advice = ComfortService._advices_from_rules(weather_forecast)

        return ComfortDTO(
            temperature=comfort_values["temperature"],
            humidity=comfort_values["humidity"],
            wind_speed=comfort_values["wind_speed"],
            uva=comfort_values["uva"],
            aod=comfort_values["aod"],
            simple_avg=simple_avg,
            weighted_avg=weighted_avg,
            advice=advice
        )
