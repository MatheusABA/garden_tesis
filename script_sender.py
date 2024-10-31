import requests
import json
import time
from datetime import datetime

# URL do endpoint FastAPI
url = "http://127.0.0.1:8000/api/data"  # Altere para o IP e a porta do seu servidor FastAPI

# Função para enviar dados
def send_sensor_data(sensor_type, measure_type, measure_value):
    try:
        # Estrutura do pacote de dados
        data = {
              "data": [
                    {
                        "sensor_type": sensor_type,
                        "measure_type": measure_type,
                        "measure_value": measure_value,
                        "timestamp": datetime.now().isoformat()  # Gera um timestamp no formato ISO 8601  }     
                    }
            ]
        }
            
            
        

        # Enviar a requisição POST
        response = requests.post(url, json=data)

        # Verificar a resposta
        if response.status_code != 50:
            print("Dados enviados com sucesso:", response.json())
        else:
            print("Falha ao enviar dados:", response.status_code, response.text)
    except Exception as e:
        print("Nao foi possivel enviar os dados")

# Loop para enviar dados continuamente
while True:
    # Exemplos de dados para cada sensor
    send_sensor_data("DHT11", "umidade", 60.5)  # Enviando umidade
    send_sensor_data("DHT11", "temperatura", 24.0)  # Enviando temperatura
    send_sensor_data("MQ7", "co2", 400)  # Enviando nível de CO2
    send_sensor_data("LDR", "luminosidade", 300)  # Enviando luminosidade

    # Aguarda 1 minuto antes de enviar novamente
    time.sleep(5)  # Intervalo de 1 minuto
