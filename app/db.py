import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()   # Initializing .env values

MONGODB_URL = os.getenv("MONGODB_URL")

# Creating a client with MongoDB
client = AsyncIOMotorClient(MONGODB_URL)

def get_garden_db():
    """Return connection with garden database"""
    return client[os.getenv("DATABASE")]

def get_garden_complete_db():
    """Return connection with garden_complete database"""
    return client[os.getenv("DATABASE_COMPLETE")]


def connection():
    try:
        client.admin.command("Ping")
        print("Connection succesfull")
    except Exception as e:
        print(e)
        

if __name__ == "__main__":
    import asyncio
    asyncio.run(connection())
    