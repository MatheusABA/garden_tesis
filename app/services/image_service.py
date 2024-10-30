import logging
import cv2
import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv


load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
db = client['garden']  
collection = db['images']  

async def save_image_to_db(image_filename):
    with open(image_filename, "rb") as image_file:
        image_data = image_file.read()
    
    try:
        # Armazenando a imagem no MongoDB
        await collection.insert_one({
            "image_data": image_data,
            "timestamp": datetime.datetime.utcnow()
        })
        
    except Exception as e:
        logging.error("Erro ao salvar imagens no Banco de Dados", e)

async def capture_image():
    ip = "192.168.0.102"
    camera_url = f'http://{ip}:8080/video'
    cap = cv2.VideoCapture(camera_url)
    
    if not cap.isOpened():
        logging.error("Erro ao acessar a câmera.")
        return
    
    ret, frame = cap.read()
    
    if ret:
        # print("Camera encontrada")
        # Gerando um nome de arquivo baseado na data e hora atual
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_directory = "../../images"
        os.makedirs(save_directory, exist_ok=True)
        image_filename = os.path.join(save_directory, f"image_{timestamp}.jpg")
        
        # Salvando a imagem localmente
        if cv2.imwrite(image_filename, frame):
            logging.info(f"Imagem capturada e salva como {image_filename}")
            print(f"Imagem captura e salva como {image_filename}")

            # Salvando a imagem no MongoDB
            await save_image_to_db(image_filename)

            # Linha para remover imagem local após ele salvar no banco
            os.remove(image_filename)
        else:
            logging.error("Erro ao capturar a imagem.")

        return image_filename
    
    cap.release()

async def main():
    while True:
        await capture_image()
        await asyncio.sleep(10)  # Espera 24 horas (86400 segundos)

if __name__ == "__main__":
    asyncio.run(main())
