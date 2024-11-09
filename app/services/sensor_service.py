from ..db import get_garden_db
import json
import os
import logging
from .image_service import capture_image
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from pytz import timezone
from zoneinfo import ZoneInfo

# Logs de erros
logging.basicConfig(level=logging.INFO) 

# Buffer para armazenar temporariamente os dados dos sensores
sensor_data_buffer = []
# Defina o limite de dados a serem acumulados (60 = 1hora)
BUFFER_LIMIT = 24
# Caminho do arquivo json salvo temporariamente antes de ser enviado ao banco se desejar
BUFFER_FILE_PATH = "sensor_data.json"
HOURLY_DATA_DIR = "data/hourly_data"
DAILY_DATA_DIR = "data/daily_data"

utc = timezone("America/Cuiaba")

os.makedirs(HOURLY_DATA_DIR, exist_ok=True)
os.makedirs(DAILY_DATA_DIR, exist_ok=True)


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
            await save_hourly_data(mean, original_json)
            
            sensor_data_buffer.clear()
            
        except Exception as e:
            logging.error("Erro ao processar matriz horária", exc_info=e)
            return {"status": "Erro ao processar matriz horária", "error": str(e)}

    return  {
        "status": "Dados armazenados no buffer e serão salvos quando o buffer estiver cheio!",
        "insert_id": None
    }


async def save_hourly_data(mean, original_json):
    "Salva dados horarios na collection hourly_data e localmente"
    garden_db = await get_garden_db()
    # print(f"Teste - {original_json}")
    try:
        # original_json = original_json.tolist()  # Converte para lista

        hourly_data = {
            "timestamp": original_json["timestamp"],  # Adiciona timestamp atual
            "sensor_mean": mean,
            "processed": False
        }

        logging.info("Tentando salvar dados horários: %s", hourly_data)
        
        # Armazena no banco - COMENTAR LINHA CASO ARMAZENAMENTO SEJA SOMENTE LOCAL
        await garden_db.hourly_data.insert_one(hourly_data) 
        
        save_local_data(hourly_data, HOURLY_DATA_DIR, "hourly")
        
        
        logging.info("Dados horários salva com sucesso!")
    except Exception as e:
        logging.error("Erro ao salvar dados horários", e)


# ------------------------------- ARMAZENAMENTO DE DADOS DIARIOS -----------------------------------
async def save_daily_data(daily_data):
    """Salva os dados diários na collection 'daily_data' e localmente."""
    garden_db = await get_garden_db()

    try:
        # Salva os dados diários no banco de dados
        await garden_db.daily_data.insert_one(daily_data)

        # Salva os dados localmente, se necessário
        save_local_data(daily_data, DAILY_DATA_DIR, "daily")

        logging.info("Dados diários salvos com sucesso!")
    except Exception as e:
        logging.error(f"Erro ao salvar dados diários: {str(e)}")


# ------------------------------- ARMAZENAMENTO DE DADOS HORARIOS -----------------------------------
async def save_hourly_json(original_json):
    "Salva json original para o usuario realizar quais metricas ele quiser"
    garden_db = await get_garden_db()
    try:
        # logging.info("Tentando salvar JSON original: %s", original_json)
        await garden_db.hourly_json.insert_one(original_json)
        logging.info("JSON original salvo com sucesso.")
                
                
    except Exception as e:
        logging.error("Erro ao salvar json original: %s", e)
        logging.info("Estrutura do original_json: %s", type(original_json))



# ------------------------------- FUNCAO PARA ARMAZENAR DADOS -----------------------------------
def save_local_data(data, directory, data_type):
    """Salva dados localmente em um arquivo JSON na pasta específica."""
    timestamp_str = datetime.now().astimezone(utc)
    file_path = os.path.join(directory, f"{data_type}_data_{timestamp_str.strftime("%Y-%m-%d_%H-%M-%S")}.json")
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4, default=str)
        logging.info(f"{data_type.capitalize()} data salvo localmente em {file_path}")
    except Exception as e:
        logging.error(f"Erro ao salvar {data_type} data localmente", exc_info=True)



# -------------------------- FUNCAO PARA PROCESSAMENTO DE MEDIA -----------------------------------
def process_mean(data):
    """Processa os dados dos sensores para realizar a média (Horária ou Diária)"""

    try:
        measures = {
            'UMIDADE': [],
            'TEMPERATURA': [],
            'CO': [],
            'LUMINOSIDADE': []
        }
        
        # Preenchendo as listas de medidas com base nos dados recebidos
        for entry in data['data']:
            measure_type = entry['measure_type']
            measure_value = entry['measure_value']
            if measure_type in measures:
                measures[measure_type].append(measure_value)
        

        means = {}

        for measure_type, values in measures.items():
            if values:
                # Calcular a média dos valores
                means[measure_type] = round(sum(values)/len(values), 2)
        return  means
    
    except Exception as e:
        logging.error("Erro ao processar dados: %s", e)
        return None


async def process_daily_data():
    """Processa as matrizes horárias para criar uma matriz diária e salva na coleção 'daily_data'."""
    try:
        logging.info("Tentando processar a matriz diária")
        garden_db = await get_garden_db()

        # Coleta todas as matrizes horárias não processadas
        current_date = datetime.now().date()
        hourly_data_entries = await garden_db.hourly_data.find({"processed": False}).to_list(length=None)
        logging.info(hourly_data_entries)
        if not hourly_data_entries:
            logging.info("Não há matrizes disponíveis para realizar a matriz diária")
            return {"status": "Não há matrizes disponíveis para realizar a matriz diária"}

        # Verifica se as matrizes horárias possuem valores válidos
        if not all(entry.get("sensor_mean") for entry in hourly_data_entries):
            logging.error("Algumas matrizes horárias não possuem valores válidos.")
            return {"status": "Erro ao processar matrizes horárias"}

        # Calcula a média diária para cada sensor (UMIDADE, TEMPERATURA, CO, LUMINOSIDADE)
        sensor_means = {
            "UMIDADE": [],
            "TEMPERATURA": [],
            "CO": [],
            "LUMINOSIDADE": []
        }

        # Preenche as listas com os valores dos sensores de todas as entradas horárias
        for entry in hourly_data_entries:
            for sensor, value in entry["sensor_mean"].items():
                sensor_means[sensor].append(value)

        # Calcula a média de cada sensor
        mean_daily = {sensor: np.mean(values) for sensor, values in sensor_means.items()}

        # Captura e salva a imagem do plantio
        image_filename = await capture_image()  # Retorna o caminho da imagem capturada

        # Estrutura a matriz diária com a média calculada e a imagem
        daily_data = {
            "timestamp": datetime.now().astimezone(utc).strftime("%Y-%m-%d_%H-%M-%S"),
            "sensor_mean": mean_daily,
            "image_filename": image_filename,  # Inclui o caminho da imagem
        }

        # Chama save_daily_data para salvar os dados processados
        await save_daily_data(daily_data)  # Passa todos os dados necessários para salvar

        # Marca as matrizes horárias como processadas
        for entry in hourly_data_entries:
            await garden_db.hourly_data.update_one(
                {"_id": entry["_id"]},
                {"$set": {"processed": True}}  # Atualiza o status das matrizes horárias
            )

        return {"status": "Matriz diária salva com sucesso"}

    except Exception as e:
        logging.error(f"Não foi possível processar a matriz diária: {str(e)}")
        return {"status": "Erro ao processar matriz diária", "error": str(e)}


# ---------------------------- SOMENTE LEITURA DE DADOS ------------------------
from bson import ObjectId

def convert_object_id(data):
    """Recursively converts ObjectId to string in MongoDB documents."""
    if isinstance(data, list):
        return [convert_object_id(item) for item in data]
    elif isinstance(data, dict):
        return {key: (str(value) if isinstance(value, ObjectId) else convert_object_id(value)) for key, value in data.items()}
    else:
        return data
    
    
async def get_hourly_data():
    garden_db = await get_garden_db()
    try:
        data = await garden_db.hourly_data.find().to_list(length=None)
        data = convert_object_id(data)  # Converte ObjectIds para strings
        return {"status": "success", "data": data}
    except Exception as e:
        logging.error("Erro ao obter matrizes horárias: %s", e)
        return {"status": "error", "message": str(e)}

async def get_daily_data():
    garden_db = await get_garden_db()
    try:
        data = await garden_db.daily_data.find().to_list(length=None)
        data = convert_object_id(data)  # Converte ObjectIds para strings
        return {"status": "success", "data": data}
    except Exception as e:
        logging.error("Erro ao obter matrizes diárias: %s", e)
        return {"status": "error", "message": str(e)}

async def get_images():
    garden_db = await get_garden_db()
    try:
        images = await garden_db.images.find().to_list(length=None)
        images = convert_object_id(images)  # Converte ObjectIds para strings
        return {"status": "success", "data": images}
    except Exception as e:
        logging.error("Erro ao obter imagens: %s", e)
        return {"status": "error", "message": str(e)}

async def get_original_json():
    garden_db = await get_garden_db()
    try:
        original_json = await garden_db.hourly_json.find().to_list(length=None)
        original_json = convert_object_id(original_json)  # Converte ObjectIds para strings
        return {"status": "success", "data": original_json}
    except Exception as e:
        logging.error("Erro ao obter JSON original: %s", e)
        return {"status": "error", "message": str(e)}