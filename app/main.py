from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .controllers.sensor_controller import router as sensor_router
from .services.sensor_service import process_daily_data
from .db import connection
import asyncio
import logging
import uvicorn

#  FastAPI Description
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# Routes
app.include_router(sensor_router, prefix="/api")  # Sensor Route

# ------------ App Events
# Startup
@app.on_event("startup")
async def startup_event():
    try:
        await connection()        # Database connection
        asyncio.create_task(schedule_daily_processing())    
    except Exception as e:
        logging.error("Erro ao iniciar aplicação")

async def schedule_daily_processing():
    """Agenda o processamento da matriz diária a cada 24 horas."""
    while True:
        await process_daily_data()
        await asyncio.sleep(30)  # 86400 = Espera 24 horas
