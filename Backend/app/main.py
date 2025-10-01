from dotenv import load_dotenv

load_dotenv()

import logging
from fastapi import FastAPI
from app.api.weather_router import router as weather_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    force=True,
)

app = FastAPI(title="Weather API with SOLID")

app.include_router(weather_router)
@app.get("/")
async def root():
    return {"message": "Weather API працює! Використовуй /weather/forecast?city=Kyiv"}
