from pydantic import BaseModel      # Data validation
from typing import List

# Data Model
class SensorData(BaseModel):
    sensor_id: str
    measure_type: str
    measure_value: str
    timestamp: str
    
    
class PackageData(BaseModel):
    pending: bool
    data: List[SensorData]
