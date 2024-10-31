from ..db import get_garden_db
import json
import os
import logging
from .image_service import capture_image
import numpy as np
from datetime import datetime

# Logs de erros
logging.basicConfig(level=logging.INFO) 

# Buffer para armazenar temporariamente os dados dos sensores
sensor_data_buffer = []
BUFFER_LIMIT = 4  # Defina o limite de dados a serem acumulados (60 = 1hora)

BUFFER_FILE_PATH = "sensor_data.json"


def save_buffer_locally(buffer):
    """Salva o conteúdo do buffer em um arquivo JSON localmente."""
    try:
        with open(BUFFER_FILE_PATH, 'w') as f:
            json.dump(buffer, f, indent=4, default=str)
        logging.info("Buffer salvo localmente em %s", BUFFER_FILE_PATH)
    except Exception as e:
        logging.error("Erro ao salvar buffer localmente", exc_info=True)




async def store_sensor_data(package_data):
        
    # PEGAR DADOS DOS SENSORES, ENCAPSULAR
    
    if not package_data.data:
        logging.warning("Nenhum dado disponível")
        return {"status": "No data provided", "inserted_id": []}
    
    # Adiciona os dados no buffer
    for sensor_data in package_data.data:
        sensor_data_buffer.append(sensor_data.dict())
        
    # sensor_data_buffer.append(package_data.data)
        
    
        
    save_buffer_locally(sensor_data_buffer)

    if  len(sensor_data_buffer) >= BUFFER_LIMIT:
        try:
            # Construindo matriz horaria
            timestamp = package_data.data[0].timestamp
            
            
            hourly_correlation = process_to_hourly_correlation({
                "data": sensor_data_buffer,
                "timestamp": timestamp,
            })
            
            original_json = {
                "data": sensor_data_buffer,
                "timestamp": timestamp
            }
            
            if hourly_correlation is None:
                logging.error("Erro no processamento dos dados de correlação horária.")
                
    
            await save_hourly_json(original_json)
            await save_hourly_correlation(hourly_correlation)
            
            sensor_data_buffer.clear()
            
        except Exception as e:
            logging.error("Erro ao processar matriz horária", exc_info=e)
            return {"status": "Erro ao processar matriz horária", "error": str(e)}
        
        

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
        logging.info("Tentando salvar JSON original: %s", original_json)
        await garden_db.hourly_json.insert_one(original_json)
        logging.info("JSON original salvo com sucesso.")
            
            
    except Exception as e:
        logging.error("Erro ao salvar json original: %s", e)
        logging.info("Estrutura do original_json: %s", type(original_json))
        
    
    
    
    
def process_to_hourly_correlation(data):
    """Processa o buffer e gera a matriz horária e JSON dos dados."""
    try :
        logging.info("Dados recebidos para correlação horária: %s", data)
        
        sensor_values = np.array([list(d.values()) for d in data["data"]])
        # sensor_values = []
        # for d in data["data"]:
        #     sensor_values.append(float(d['measure_value']))
        
        # sensor_values = np.array(sensor_values)
        
        correlation_matrix = np.corrcoef(sensor_values, rowvar=False)
        # correlation_matrix = np.corrcoef(sensor_values.reshape(-1, len(data["data"])), rowvar=False)
        
        # Cria a matriz horária como uma média dos dados
        hourly_correlation = {
            "timestamp": data["timestamp"],
            "correlation_matrix": correlation_matrix.tolist(),
            "processed": False
        }        
        
        logging.info(hourly_correlation)
        return hourly_correlation
    
    except Exception as e:
        logging.error("Não foi possível processar a correlação diária")
        return None, None
        
    
    

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