from pydantic import BaseModel      # Data validation
from typing import List

# Data Model
class SensorData(BaseModel):
    sensor_id: str
    measure_type: str
    measure_value: str
    timestamp: str
    
    
class PackageData(BaseModel):
    pending: bool   # Utilizado para realizar os cálculos de correalação diários
    tag: str        # Utilizado para identificar se é uma correlação horária ou diária
    data: List[SensorData]
