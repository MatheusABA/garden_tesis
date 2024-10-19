from fastapi import APIRouter, HTTPException
from ..models import PackageData
from ..services.sensor_service import store_sensor_data

# Encapsulando todas as rotas aqui
router = APIRouter()

@router.post("/data")
async def store_data(package_data: PackageData):
    result =  await store_sensor_data(package_data)
    if result["inserted_id"] is None:
        raise HTTPException(status_code=400, detail=result["status"]) 
    
    return result

