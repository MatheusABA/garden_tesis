from fastapi import APIRouter, HTTPException, UploadFile, File
from ..models import PackageData
from ..services.sensor_service import store_sensor_data, get_daily_data, get_hourly_data, get_images, get_original_json

# Encapsulando todas as rotas aqui
router = APIRouter()

@router.post("/data")
async def store_data(package_data: PackageData):
    print(package_data)
    result =  await store_sensor_data(package_data)
    return result


@router.get("/hourly_data")
async def fetch_hourly_data():
    """Retorna todas os dados horários salvas no banco."""
    response = await get_hourly_data()
    if response['status'] == "error":
        raise HTTPException(status_code=500, detail=response['message'])
    if not response['data']:
        raise HTTPException(status_code=404, detail="No hourly data found")
    return response

@router.get("/daily_data")
async def fetch_daily_data():
    """Retorna todas os dados diários salvas no banco."""
    response = await get_daily_data()
    if response['status'] == "error":
        raise HTTPException(status_code=500, detail=response['message'])
    if not response['data']:
        raise HTTPException(status_code=404, detail="No daily data found")
    return response

@router.get("/json")
async def fetch_original_json():
    """Retorna o JSON original salvo no banco."""
    response = await get_original_json()
    if response['status'] == "error":
        raise HTTPException(status_code=500, detail=response['message'])
    if not response['data']:
        raise HTTPException(status_code=404, detail="No original json found")
    return response

@router.get("/images")
async def fetch_images():
    """Retorna todas as imagens salvas no banco."""
    response = await get_images()
    if response['status'] == "error":
        raise HTTPException(status_code=500, detail=response['message'])
    if not response['data']:
        raise HTTPException(status_code=404, detail="No images found")
    return response