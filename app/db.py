import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()   # Initializing .env values

MONGODB_URL = os.getenv("MONGODB_URL")

# Creating a client with MongoDB
client = AsyncIOMotorClient(MONGODB_URL)

async def initialize_database():
    """Inicializa o banco de dados e garante que todas as coleções necessárias existam."""
    db = client[os.getenv("DATABASE")]
    collections = ["hourly_data", "hourly_json", "daily_data", "images"]
    existing_collections = await db.list_collection_names()

    for collection in collections:
        if collection not in existing_collections:
            await db.create_collection(collection)
            print(f"Collection '{collection}' criada.")
        else:
            print(f"Collection '{collection}' já existe.")

async def get_garden_db():
    """Retorna conexão com o banco de dados garden"""
    return client[os.getenv("DATABASE")]


async def connection():
    try:
        client.admin.command("Ping")
        print("Connection succesfull")
        await initialize_database()
    except Exception as e:
        print(e)
        

if __name__ == "__main__":
    import asyncio
    asyncio.run(connection())
    