from pymongo import ReturnDocument
from ..db import get_garden_db


# Buffer para armazenar temporariamente os dados dos sensores
sensor_data_buffer = []
BUFFER_LIMIT = 4  # Defina o limite de dados a serem acumulados


async def store_sensor_data(package_data):
    # Store sensor in a list, waiting the time to do the correalation and save this
    
    if not package_data.data:
        return {"status": "No data provided", "inserted_id": []}
    
    # Adiciona os dados no buffer
    sensor_data_buffer.append(package_data.data)

    if  len(sensor_data_buffer) >= BUFFER_LIMIT:

        # Use timestamps in last position
        timestamp = package_data.data.timestamp[0]
        combined_data = {
            "timestamp": timestamp,
            "data": [sensor_data.model_dump() for sensor_data in package_data.data]
        }

        data_correlation(combined_data)

    return  {
        "status": "Data is being buffered, will be saved when the buffer is full",
        "insert_id": None
    }


async def data_correlation(data):
    print(data)
    garden_db = get_garden_db()
    result = await garden_db.sensor_data.insert_one(data)
        
    return {
        "status": "The data was successfully saved on storage",
        "inserted_id": str(result.inserted_id)
    }