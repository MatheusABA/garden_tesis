from pydantic import BaseModel      # Data validation
from typing import List, Optional

# Data Model
class SensorData(BaseModel):
    sensor_type: str
    measure_type: str
    measure_value: str
    timestamp: str
    
    
class PackageData(BaseModel):
    data: List[SensorData]

# Modelo para a Matriz Horária
class HourlyMatrix(BaseModel):
    timestamp: str  # Timestamp representativo da matriz
    mean_values: List[float]  # Valores médios das medições dos sensores
    processed: Optional[bool] = False  # Indica se já foi processada para a matriz diária

# Modelo para a Matriz Diária
class DailyMatrix(BaseModel):
    timestamp: str  # Timestamp da criação da matriz diária
    mean_values: List[float]  # Valores médios diários dos sensores
    image_filename: str  # Nome do arquivo da imagem associada
    