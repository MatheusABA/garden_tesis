from fastapi import FastAPI
from pydantic import BaseModel
from .db import db
from typing import List

app = FastAPI();


# Data Model
class SensorData(BaseModel):
    sensor_id: str
    measure_type: str
    measure_value: str
    timestamp: str
    
    
class PackageData(BaseModel):
    data: List[SensorData]


# Routes
@app.get("/")
def root():
    return {"message": "Welcome to our monitoring service!"}


@app.post("/data")
async def store_data(package_data: PackageData):
    
    if not package_data.data:
        return {"status": "No data provided", "inserted_id": []}

    # Use timestamps of the first sensor as reference
    timestamp = package_data.data[0].timestamp
    
    
    combined_data = {
        "timestamp": timestamp,
        "measurements": [sensor_data.model_dump() for sensor_data in package_data.data]
    }
        
    # Inserting the data
    result = db.sensor_data.insert_one(combined_data)
    
    return {
        "status": "The data was successfully saved on storage",
        "inserted_id": str(result.inserted_id)
    }
        


