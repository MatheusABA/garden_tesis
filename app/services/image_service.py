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

async def save_image_to_db(image_filename, processed_image):
    try:
        # Converte a imagem processada para bytes para armazenamento
        _, buffer = cv2.imencode('.jpg', processed_image)
        image_data = buffer.tobytes()

        # Armazenando a imagem processada no MongoDB
        await collection.insert_one({
            "image_data": image_data,
            "timestamp": datetime.datetime.utcnow()
        })
        logging.info("Imagem processada salva no MongoDB com sucesso.")
        
    except Exception as e:
        logging.error(f"Erro ao salvar imagem processada no Banco de Dados: {e}")

def preprocess_image(image):
    """
    Realiza o pré-processamento da imagem capturada:
    - Redimensiona para 256x256 pixels
    - Converte para tons de cinza
    - Aplica suavização Gaussiana
    - Aplica detecção de bordas com Canny
    """
    # Redimensiona a imagem
    resized_image = cv2.resize(image, (256, 256))

    # Converte para tons de cinza
    # gray_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)

    # Suavização com filtro Gaussiano para reduzir ruído
    # blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

    # Detecção de bordas
    edges = cv2.Canny(resized_image, 50, 150)

    return edges

async def capture_image():
    ip = "192.168.0.124"
    port = "8090"
    camera_url = f'http://{ip}:{port}/shot.jpg'
    cap = cv2.VideoCapture(camera_url)
    
    if not cap.isOpened():
        logging.error("Erro ao acessar a câmera.")
        return None
    
    ret, frame = cap.read()
    
    # Sempre libere a câmera, independentemente do resultado
    cap.release()
    
    if ret:
        # Pré-processa a imagem antes de salvar
        processed_image = frame
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_directory = "./images"  # Use caminho relativo ou absoluto conforme necessário
        os.makedirs(save_directory, exist_ok=True)
        image_filename = os.path.join(save_directory, f"image_{timestamp}_processed.jpg")
        
        # Salvando a imagem processada localmente
        if cv2.imwrite(image_filename, processed_image):
            logging.info(f"Imagem capturada e salva como {image_filename}")
            
            # Salva a imagem processada no banco de dados
            await save_image_to_db(image_filename, processed_image)

            # Remove a imagem local após salvar no banco, se desejado
            # os.remove(image_filename)
        else:
            logging.error("Erro ao salvar a imagem localmente.")
            return None
        
        # Retorna o caminho da imagem salva (relativo ao sistema de arquivos)
        return image_filename
    
    logging.error("Erro ao capturar a imagem.")
    return None

async def main():
    while True:
        await capture_image()
        await asyncio.sleep(10)  # Espera 10 segundos entre capturas

if __name__ == "__main__":
    asyncio.run(main())
