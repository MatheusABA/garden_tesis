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
            
            # Processamento da matriz horária
            hourly_correlation = process_to_hourly_correlation({
                "data": sensor_data_buffer,
                "timestamp": timestamp,
            })

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
            await save_hourly_correlation(hourly_correlation, mean, original_json)
            
            sensor_data_buffer.clear()
            
        except Exception as e:
            logging.error("Erro ao processar matriz horária", exc_info=e)
            return {"status": "Erro ao processar matriz horária", "error": str(e)}

    return  {
        "status": "Dados armazenados no buffer e serão salvos quando o buffer estiver cheio!",
        "insert_id": None
    }


async def save_hourly_correlation(hourly_correlation, mean, original_json):
    "Salva matriz horaria na colleciton hourly_matrices"
    garden_db = await get_garden_db()
    print(f"Teste - {hourly_correlation}")
    try:
        if isinstance(hourly_correlation, np.ndarray):
            hourly_correlation = hourly_correlation.tolist()  # Converte para lista
            correlation_data = {
            "timestamp": datetime.utcnow(),  # Adiciona timestamp atual
            "correlation_matrix": hourly_correlation,
            "sensor_mean": mean,
            "processed": False
        }
        logging.info("Tentando salvar correlação horária: %s", hourly_correlation)
        await garden_db.hourly_correlation.insert_one(correlation_data)
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


def process_to_hourly_correlation(data):
    """Processa o buffer e gera a matriz horária e JSON dos dados."""
    
    try :        
        # TESTES PARA SALVAR CADA VALOR DOS SENSORES EM DICIONARIO PARA PASSAR AO CORRCOE DO NUMMPY
        # Dicionário para organizar valores de cada tipo de medida
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

        print(f"SERIES DATA\033[91m {series_data} \033[00m")
        # Verifica se todos os tipos de medida têm dados suficientes para calcular a correlação
        if all(len(values) > 1 for values in series_data):
            # Calcula a matriz de correlação
            hourly_correlation = np.corrcoef(series_data)
            return hourly_correlation
        else:
            print("Erro: Dados insuficientes para uma ou mais variáveis.")
            return None
    
    except Exception as e:
        logging.error("Não foi possível processar a correlação diária")
        return None, None
        

async def process_daily_correlation():
    """Processa as matrizes horárias para criar uma matriz diária e salva na coleção 'daily_matrices'."""
    try:
        logging.info("TENTANDO SALVAR MATRIZ DIARIA")
        garden_db = await get_garden_db()
        
        # Coleta todas as matrizes horárias do dia
        current_date = datetime.now().date()
        hourly_correlations = await garden_db.hourly_correlations.find({"processed": False}).to_list(length=None)

        if not hourly_correlations:
            logging.info(f"{datetime.now()} - Não há matrizes disponíveis para realizar a matriz diária")
            return {"status": "Não há matrizes disponíveis para realizar a matriz diária"}

        # Verifica se as matrizes horárias têm valores válidos
        if not all(entry.get("mean_values") is not None for entry in hourly_correlations):
            logging.error("Algumas matrizes horárias não possuem valores válidos.")
            return {"status": "Erro ao processar matrizes horárias"}

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
        logging.info(f"{datetime.now()} - MATRIZ DIARIA SALVA COM SUCESSO")
        
        # Atualiza as matrizes para processadas agora
        for entry in hourly_correlations:
            await garden_db.hourly_correlation.update_one(
                {"_id": entry["_id"]},
                {"$set": {"processed": True}}
            )
            
        return {"status": "Matriz diária salva com sucesso"}
    
    except Exception as e:
        logging.error(f"{datetime.now()} - Não foi possível processar a matriz diária: {str(e)}")


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
        