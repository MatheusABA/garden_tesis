import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()   # Initializing .env values

MONGODB_URL = os.getenv("MONGODB_URL")

client = MongoClient(MONGODB_URL, server_api=ServerApi("1"))

def connection():
    try:
        client.admin.command("Ping")
        print("Connection succesfull")
    except Exception as e:
        print(e)
        
        
db = client[os.getenv("DATABASe")];

if __name__ == "__main__":
    connection()
    