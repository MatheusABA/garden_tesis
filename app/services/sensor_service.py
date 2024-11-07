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
BUFFER_LIMIT = 36  # Defina o limite de dados a serem acumulados (60 = 1hora)
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
    "PEGAR DADOS DOS SENSORES, ENCAPSULAR"
    
    if not package_data.data:
        logging.warning("Nenhum dado disponível")
        return {"status": "No data provided", "inserted_id": []}
        
    # Adiciona os dados no buffer
    for sensor_data in package_data.data:
        print(f"\033[91m {sensor_data.dict()} \033[00m")
        sensor_data_buffer.append(sensor_data.dict())
    # sensor_data_buffer.append(package_data.data)
    save_buffer_locally(sensor_data_buffer)  

    if  len(sensor_data_buffer) >= BUFFER_LIMIT:
        try:
            # Construindo matriz horaria
            timestamp = package_data.data[0].timestamp

            mean = process_mean({
                "data": sensor_data_buffer,
                "timestamp": timestamp,
            })
            
            # Encapsulando json original para salvar no banco 
            original_json = {
                "data": sensor_data_buffer,
                "timestamp": timestamp
            }
                            
            await save_hourly_json(original_json)
            await save_hourly(mean, original_json)
            
            sensor_data_buffer.clear()
            
        except Exception as e:
            logging.error("Erro ao processar matriz horária", exc_info=e)
            return {"status": "Erro ao processar matriz horária", "error": str(e)}

    return  {
        "status": "Dados armazenados no buffer e serão salvos quando o buffer estiver cheio!",
        "insert_id": None
    }


async def save_hourly(mean, original_json):
    "Salva matriz horaria na colleciton hourly_matrices"
    garden_db = await get_garden_db()
    print(f"Teste - {original_json}")
    try:
        original_json = original_json.tolist()  # Converte para lista
        hourly_data = {
        "timestamp": datetime.utcnow(),  # Adiciona timestamp atual
        "sensor_mean": mean,
        "processed": False
        }

        logging.info("Tentando salvar dados horários: %s", original_json)
        await garden_db.hourly_correlation.insert_one(hourly_data)
        logging.info("Matriz horária salva com sucesso!")
    except Exception as e:
        logging.error("Erro ao salvar matriz horária")


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
        

def process_mean(data):
    """Processa os dados dos sensores para realizar a média (Horária ou Diária)"""

    try:
        measures = {
            'UMIDADE RELATIVA AR': [],
            'UMIDADE RELATIVA SOLO': [],
            'TEMPERATURA AR': [],
            'TEMPERATURA SOLO': [],
            'CO': [],
            'LUMINOSIDADE': []
        }
        
        # Preenchendo as listas de medidas com base nos dados recebidos
        for entry in data['data']:
            measure_type = entry['measure_type']
            measure_value = entry['measure_value']
            if measure_type in measures:
                measures[measure_type].append(measure_value)
        
        # Cria uma matriz onde cada linha representa uma série de dados de medida
        series_data = [
            measures['UMIDADE RELATIVA AR'],
            measures['UMIDADE RELATIVA SOLO'],
            measures['TEMPERATURA AR'],
            measures['TEMPERATURA SOLO'],
            measures['CO'],
            measures['LUMINOSIDADE']
        ]

        means = []

        for line in series_data:
            if len(line) > 0:
                # Calcular a média dos valores
                means.append(sum(line) / len(line))
        return  means
    
    except Exception as e:
        logging.error("Erro ao processar dados: %s", e)
        return None


# SOMENTE LEITURA DE DADOS
async def get_hourly_matrices():
    garden_db = await get_garden_db()
    try:
        matrices = await garden_db.hourly_correlation.find().to_list(length=None)
        return {"status": "success", "data": matrices}
    except Exception as e:
        logging.error("Erro ao obter matrizes horárias: %s", e)
        return {"status": "error", "message": str(e)}


async def get_daily_matrices():
    garden_db = await get_garden_db()
    try:
        matrices = await garden_db.daily_correlation.find().to_list(length=None)        
        return {"status": "success", "data": matrices}
    except Exception as e:
        logging.error("Erro ao obter matrizes diárias: %s", e)
        return {"status": "error", "message": str(e)}


async def get_images():
    garden_db = await get_garden_db()
    try:
        images = await garden_db.images.find().to_list(length=None)        
        return {"status": "success", "data": images}
    except Exception as e:
        logging.error("Erro ao obter imagens: %s", e)
        return {"status": "error", "message": str(e)}


async def get_original_json():
    garden_db = await get_garden_db()
    try:
        original_json = await garden_db.original_json.find().to_list(length=None)        
        return {"status": "success", "data": original_json}
    except Exception as e:
        logging.error("Erro ao obter JSON original: %s", e)
        return {"status": "error", "message": str(e)}
        