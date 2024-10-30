import requests
import json
import time

# URL do endpoint FastAPI
url = "http://127.0.0.1:8000/api/data"  # Altere para o IP e a porta do seu servidor FastAPI

# Função para enviar dados
def send_data(umidade, temperatura, co2, luminosidade):
    # Estrutura do pacote de dados
    data = {
        "umidade": umidade,
        "temperatura": temperatura,
        "co2": co2,
        "luminosidade": luminosidade
    }

    # Enviar a requisição POST
    response = requests.post(url, json=data)

    # Verificar a resposta
    if response.status_code == 200:
        print("Dados enviados com sucesso:", response.json())
    else:
        print("Falha ao enviar dados:", response.status_code, response.text)

# Loop para enviar dados continuamente
while True:
    # Valores de exemplo para cada sensor
    umidade = 60.5  # Exemplo de umidade
    temperatura = 24.0  # Exemplo de temperatura
    co2 = 400  # Exemplo de nível de CO2 em ppm
    luminosidade = 300  # Exemplo de luminosidade

    send_data(umidade, temperatura, co2, luminosidade)

    # Aguarda 1 minuto antes de enviar novamente
    time.sleep(60)  # Intervalo de 1 minuto
