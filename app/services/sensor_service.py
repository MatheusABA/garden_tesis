from pymongo import ReturnDocument
from ..db import get_garden_db


async def store_sensor_data(package_data):
    # Store sensor data on garden data
    
    if not package_data.data:
        return {"status": "No data provided", "inserted_id": []}

    # Use timestamps of the first sensor as reference
    timestamp = package_data.data[0].timestamp
    combined_data = {
        "timestamp": timestamp,
        "data": [sensor_data.model_dump() for sensor_data in package_data.data]
    }

    garden_db = get_garden_db()
    result = await garden_db.sensor_data.insert_one(combined_data)
    
    return {
        "status": "The data was successfully saved on storage",
        "inserted_id": str(result.inserted_id)
    }
