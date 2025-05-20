from fastapi import APIRouter
from typing import Optional
from fastapi import Query
from app.services.farmbot_service import FarmBotService

router = APIRouter()
farmbot_service = FarmBotService()

@router.get("/status")
@router.get("/device")
def read_status():
    return farmbot_service.get_status()

@router.post("/move")
def move_bot(
    x: Optional[int] = Query(None),
    y: Optional[int] = Query(None),
    z: Optional[int] = Query(None),
    safe_z: Optional[int] = Query(None),
    speed: Optional[float] = Query(None),
    override: Optional[bool] = Query(False),
):
    return farmbot_service.move(x, y, z, safe_z, speed, override)


@router.get("/garden_size")
def garden_size():
    return farmbot_service.garden_size()

@router.post("/toast")
def toast(message: str):
    return farmbot_service.toast(message)

@router.post("/grid_travel")
def grid_travel(start_x: int = 0, start_y: int = 0, width: int = None, length: int = None, rows: int = None, columns: int = None):
    return farmbot_service.grid_travel(start_x, start_y, width, length, rows, columns)

@router.post("/lock")
def lock():
    return farmbot_service.lock()

@router.post("/unlock")
def unlock():
    return farmbot_service.unlock()

@router.get("/logs")
def logs():
    return farmbot_service.get_logs()

@router.post("/go_home")
def go_home():
    return farmbot_service.goto_home()