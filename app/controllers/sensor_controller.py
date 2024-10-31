from fastapi import APIRouter, HTTPException, UploadFile, File
from ..models import PackageData
from ..services.sensor_service import store_sensor_data, get_daily_matrices, get_hourly_matrices, get_images

# Encapsulando todas as rotas aqui
router = APIRouter()

@router.post("/data")
async def store_data(package_data: PackageData):
    print(package_data)
    result =  await store_sensor_data(package_data)
    return result

# @router.post("/correlation")
# async def correlate_data(package_data: PackageData):
#     result =  await store_sensor_data(package_data)
#     if result["inserted_id"] is None:
#         raise HTTPException(status_code=400, detail=result["status"]) 
    
#     return result


@router.get("/hourly_matrices")
async def fetch_hourly_matrices():
    """Retorna todas as matrizes horárias salvas no banco."""
    matrices = await get_hourly_matrices()
    if not matrices:
        raise HTTPException(status_code=404, detail="No hourly matrices found")
    return matrices

@router.get("/daily_matrices")
async def fetch_daily_matrices():
    """Retorna todas as matrizes diárias salvas no banco."""
    matrices = await get_daily_matrices()
    if not matrices:
        raise HTTPException(status_code=404, detail="No daily matrices found")
    return matrices

@router.get("/images")
async def fetch_images():
    """Retorna todas as imagens salvas no banco."""
    images = await get_images()
    if not images:
        raise HTTPException(status_code=404, detail="No images found")
    return images