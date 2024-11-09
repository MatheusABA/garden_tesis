from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .controllers.sensor_controller import router as sensor_router
from .services.sensor_service import process_daily_data
from .db import connection
import asyncio
import logging
import uvicorn
import json
from pathlib import Path
import os
import time

# FastAPI Description
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

FILE_PATH = Path(__file__).parent.parent / "sensor_data.json"

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
        await asyncio.sleep(1440)  # 86400 = Espera 24 horas

# Armazena os WebSocket clients
clients = []

# Variáveis para controle de monitoramento do arquivo
last_modified_time = None
last_data = []

def check_for_updates():
    """Verifica se o arquivo foi modificado e se os dados mudaram."""
    global last_modified_time, last_data

    # Verifica se o arquivo existe
    if FILE_PATH.exists():
        # Obtém o tempo da última modificação do arquivo
        current_modified_time = os.path.getmtime(FILE_PATH)

        # Verifica se o arquivo foi modificado desde a última vez
        if last_modified_time is None or current_modified_time > last_modified_time:
            last_modified_time = current_modified_time

            with open(FILE_PATH, "r") as file:
                data_list = json.load(file)

            # Verifica se houve alteração no conteúdo dos dados
            if data_list != last_data:
                last_data = data_list
                return True  # Dados foram alterados
    return False  # Nenhuma alteração no arquivo

@app.websocket("/ws/sensor-data")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            if check_for_updates():
                # Quando houver alteração nos dados
                if len(last_data) > 0:
                    # Retorna as quatro últimas entradas
                    data = last_data[-4:]
                    # Envia os dados para todos os clientes conectados
                    for client in clients:
                        await client.send_text(json.dumps(data))
            await asyncio.sleep(1)  # Checa as atualizações a cada 1 segundo
    except:
        clients.remove(websocket)
