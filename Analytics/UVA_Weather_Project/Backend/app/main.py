from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from app.api.weather_router import router as weather_router

app = FastAPI(title="Weather API with SOLID")

app.include_router(weather_router)
@app.get("/")
async def root():
    return {"message": "Weather API працює! Використовуй /weather/forecast?city=Kyiv"}
