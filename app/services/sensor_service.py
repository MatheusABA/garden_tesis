from ..db import get_garden_db
import logging
from .image_service import capture_image
import numpy as np
from datetime import datetime

# Logs de erros
logging.basicConfig(level=logging.INFO) 

# Buffer para armazenar temporariamente os dados dos sensores
sensor_data_buffer = []
BUFFER_LIMIT = 60  # Defina o limite de dados a serem acumulados (60 = 1hora)

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
            hourly_correlation, original_json = process_to_hourly_correlation({
                "data": sensor_data_buffer,
                "timestamp": timestamp,
            })
            
            await save_hourly_correlation(hourly_correlation)
            await save_hourly_json(original_json)
            
            sensor_data_buffer.clear()
            
        except Exception as e:
            logging.error("Erro ao processar matriz horária", e)
            sensor_data_buffer.clear()
            return e
        
        

    return  {
        "status": "Dados armazenados no buffer e serão salvos quando o buffer estiver cheio!",
        "insert_id": None
    }

async def save_hourly_correlation(hourly_correlation):
    "Salva matriz horaria na colleciton hourly_matrices"
    garden_db = await get_garden_db()
    try:
        await garden_db.hourly_correlation.insert_one(hourly_correlation)
    except Exception as e:
        logging.error("Erro ao salvar matriz diaria")




async def save_hourly_json(original_json):
    "Salva json original para o usuario realizar quais metricas ele quiser"
    garden_db = await get_garden_db()
    try:
        
        await garden_db.hourly_json.insert_one(original_json)
    except Exception as e:
        logging.error("Erro ao salvar json original", e)
    
    
    
    
def process_to_hourly_correlation(data):
    """Processa o buffer e gera a matriz horária e JSON dos dados."""
    try :
        sensor_values = np.array([list(d.values()) for d in data["data"]])
        correlation_matrix = np.corrcoef(sensor_values, rowvar=False)
        
        # Cria a matriz horária como uma média dos dados
        hourly_correlation = {
            "timestamp": data["timestamp"],
            "correlation_matrix": correlation_matrix.tolist(),
            "processed": False
        }
        
        # Retorna a matriz horária e o JSON original
        original_json = {"data": data["data"], "timestamp": data["timestamp"]}
        
        return hourly_correlation, original_json
    except Exception as e:
        logging.error("Não foi possível processar a correlação diári")
    

async def process_daily_correlation():
    """Processa as matrizes horárias para criar uma matriz diária e salva na coleção 'daily_matrices'."""
    try:
        garden_db = await get_garden_db()
        # Coleta todas as matrizes horárias do dia
        current_date = datetime.now().date()
        hourly_correlations = await garden_db.hourly_correlations.find({"processed": False}).to_list(length=None)

        if not hourly_correlations:
            return {"status": "Não há matrizes disponíveis para realizar a matriz diária"}

        # Calcula a média diária
        mean_daily_correlation = np.mean([entry["mean_values"] for entry in hourly_correlations], axis=0).tolist()
        timestamp = datetime.now()
        
        # Captura e salva a imagem do plantio
        image_filename = await capture_image()
        
        # Estrutura a matriz diária com a média calculada e a imagem
        daily_correlation = {
            "timestamp": timestamp,
            "correlation_matrix": mean_daily_correlation,
            "image_filename": image_filename
        }

        # Salva a matriz diária na coleção 'daily_matrices'
        await garden_db.daily_correlation.insert_one(daily_correlation)
        
        # Atualiza as matrizes para processadas agora
        for entry in hourly_correlations:
            await garden_db.hourly_correlation.update_one(
                {"_id": entry["_id"]},
                {"$set": {"processed": True}}
            )
            
        return {"status": "Daily matrix successfully saved"}
    except Exception as e:
        logging.error("Não foi possível processar a matriz diária")


# SOMENTE LEITURA DE DADOS
async def get_hourly_matrices():
    garden_db = await get_garden_db()
    return await garden_db.hourly_correlation.find().to_list(length=None)

async def get_daily_matrices():
    garden_db = await get_garden_db()
    return await garden_db.daily_correlation.find().to_list(length=None)

async def get_images():
    garden_db = await get_garden_db()
    return await garden_db.images.find().to_list(length=None)