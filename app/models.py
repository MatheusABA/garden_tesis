from pydantic import BaseModel      # Data validation
from typing import List, Optional

# Data Model
class SensorData(BaseModel):
    sensor_type: str
    measure_type: str
    measure_value: int
    timestamp: str
    
    
class PackageData(BaseModel):
    data: List[SensorData]

# Modelo para a Matriz Horária
class HourlyMatrix(BaseModel):
    timestamp: str  # Timestamp representativo da matriz
    correlation_matrix: Optional[List[float]] = None # Valores médios das medições dos sensores - Pode ter valor nulo
    processed: Optional[bool] = False  # Indica se já foi processada para a matriz diária

# Modelo para a Matriz Diária
class DailyMatrix(BaseModel):
    timestamp: str  # Timestamp da criação da matriz diária
    correlation_matrix: Optional[List[float]] = None  # Valores médios diários dos sensores
    image_filename: str  # Nome do arquivo da imagem associada
    