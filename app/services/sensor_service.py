from pymongo import ReturnDocument
from ..db import get_garden_db
import logging
from .image_service import capture_image
import numpy as np
from datetime import datetime

# Logs de erros
logging.basicConfig(level=logging.INFO) 

# Buffer para armazenar temporariamente os dados dos sensores
sensor_data_buffer = []
BUFFER_LIMIT = 4  # Defina o limite de dados a serem acumulados

async def store_sensor_data(package_data):
        
    # PEGAR DADOS DOS SENSORES, ENCAPSULAR
    
    if not package_data.data:
        logging.warning("Nenhum dado disponível")
        return {"status": "No data provided", "inserted_id": []}
    
    # Adiciona os dados no buffer
    sensor_data_buffer.append(package_data.data)

    if  len(sensor_data_buffer) >= BUFFER_LIMIT:
        try:
            # Construindo matriz horaria
            timestamp = package_data.data.timestamp[0]
            hourly_matrix, original_json = process_to_hourly_matrix({
                "data": sensor_data_buffer,
                "timestamp": timestamp,
            })
            
            await save_hourly_matrix(hourly_matrix)
            await save_hourly_json(original_json)
            
            sensor_data_buffer.clear()
        except Exception as e:
            sensor_data_buffer.clear()
            return e
        
        # data_correlation(combined_data)

    return  {
        "status": "Dados estão sendo bufferizados e serão salvos quando o buffer estiver cheio!",
        "insert_id": None
    }

async def save_hourly_matrix(hourly_matrix):
    "Salva matriz horaria na colleciton hourly_matrices"
    garden_db = get_garden_db()
    await garden_db.hourly_matrices.insert_one(hourly_matrix)

async def save_hourly_json(original_json):
    "Salva json original para o usuario realizar quais metricas ele quiser"
    garden_db = get_garden_db()
    await garden_db.hourly_json.insert_one(original_json)
    
def process_to_hourly_matrix(data):
    """Processa o buffer e gera a matriz horária e JSON dos dados."""
    sensor_values = np.array([list(d.values()) for d in data["data"]])
    mean_values = np.mean(sensor_values, axis=0)
    
    # Cria a matriz horária como uma média dos dados
    hourly_matrix = {
        "timestamp": data["timestamp"],
        "mean_values": mean_values.tolist()
    }
    
    # Retorna a matriz horária e o JSON original
    original_json = {"data": data["data"], "timestamp": data["timestamp"]}
    
    return hourly_matrix, original_json

async def process_daily_matrix():
    """Processa as matrizes horárias para criar uma matriz diária e salva na coleção 'daily_matrices'."""
    garden_db = get_garden_db()
    
    # Coleta todas as matrizes horárias do dia
    current_date = datetime.now().date()
    hourly_matrices = await garden_db.hourly_matrices.find({
        "timestamp": {"$gte": datetime.combine(current_date, datetime.min.time())}
    }).to_list(length=None)

    if not hourly_matrices:
        return {"status": "No hourly matrices available for the daily matrix"}

    # Calcula a média diária
    mean_daily_values = np.mean([entry["mean_values"] for entry in hourly_matrices], axis=0).tolist()
    timestamp = datetime.now()
    
    # Captura e salva a imagem do plantio
    image_filename = await capture_and_save_image()
    
    # Estrutura a matriz diária com a média calculada e a imagem
    daily_matrix = {
        "timestamp": timestamp,
        "mean_values": mean_daily_values,
        "image_filename": image_filename
    }

    # Salva a matriz diária na coleção 'daily_matrices'
    await garden_db.daily_matrices.insert_one(daily_matrix)

    return {"status": "Daily matrix successfully saved"}

async def capture_and_save_image():
    """Função para capturar uma imagem e salvar no banco."""
    from ..services.image_service import capture_image
    image_filename = await capture_image()
    return image_filename