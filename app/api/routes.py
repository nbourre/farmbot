from fastapi import APIRouter
from app.services.farmbot_service import FarmBotService

router = APIRouter()
farmbot_service = FarmBotService()

@router.get("/status")
@router.get("/device")
def read_status():
    return farmbot_service.get_status()

@router.post("/move")
def move_bot(x: int, y: int, z: int):
    return farmbot_service.move(x, y, z)

@router.get("/garden_size")
def garden_size():
    return farmbot_service.garden_size()

@router.post("/toast")
def toast(message: str):
    return farmbot_service.toast(message)