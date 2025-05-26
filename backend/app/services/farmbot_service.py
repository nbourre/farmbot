from farmbot import Farmbot
from app.utils.auth import load_token
import time
from functools import lru_cache
from app.utils.mqtt_client import FarmbotMQTTClient
import asyncio
from app.utils.zones import ZoneManager



class FarmBotService:
    def __init__(self):
        self.fb = Farmbot()
        self.token = load_token()
        self.fb.set_token(self.token)
        self.stop = False
        self.status_data = {}
        
        self.safe_height = self.fb.safe_z()
        
        # Load zones from file
        self.zone_manager = ZoneManager()
        self.zone_manager.load_from_file("app/utils/zones.json")
        
        # Initialize MQTT client
        self.mqtt = FarmbotMQTTClient(on_status=self._update_status)
        self.mqtt.connect()
        
        self._idle_event = asyncio.Event()
        if not self.is_busy():
            self._idle_event.set()
 
    def is_busy(self):
        return self.status_data.get("informational_settings", {}).get("busy", True)
       
    def _update_status(self, payload):
        self.status_data = payload
        busy = payload.get("informational_settings", {}).get("busy", True)

        if busy:
            self._idle_event.clear()
        else:
            self._idle_event.set()
            
    async def wait_until_idle(self, timeout=30):
        try:
            await asyncio.wait_for(self._idle_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def get_current_status(self):
        info = self.status_data.get("informational_settings", {})
        position = self.status_data.get("location_data", {}).get("position", {})
        axis_states = self.status_data.get("location_data", {}).get("axis_states", {})
        return {
            "busy": info.get("busy", None),
            "idle": info.get("idle", None),
            "position": position,
            "axis_states": axis_states,
            "sync_status": info.get("sync_status", None),
            "uptime": info.get("uptime", None),
            "locked": info.get("locked", None),
        }

    def get_status(self):
        return self.fb.api_get("device") # Retrieves FarmBot device status

    def move(self, x=None, y=None, z=None, safe_z=None, speed=None, override=False):
        if not override:
            # Safety limits
            if x is not None and x < 770:
                return {"status": "error", "message": "X value too low. Minimum: 770"}

            if y is not None and y < 180:
                return {"status": "error", "message": "Y value too low. Minimum: 180"}

        return self.fb.move(x, y, z, safe_z, speed)
    
    async def safe_move_to(self, x=None, y=None, z=None):
        current = self.status_data.get("location_data", {}).get("position", {})
        current_x = current.get("x")
        current_y = current.get("y")
        current_z = current.get("z")

        if current_x is None or current_y is None or current_z is None:
            return {"status": "error", "message": "Position actuelle inconnue"}
        
        #print(f"Current position: x={current_x}, y={current_y}, z={current_z}")

        final_x = x if x is not None else current_x
        final_y = y if y is not None else current_y
        final_z = z if z is not None else current_z

        crossed_forbidden = self.would_cross_forbidden_zone(final_x, final_y)
        print(f"Would cross forbidden zone: {crossed_forbidden}")
        
        final_zone = self.zone_manager.get_zone_at(final_x, final_y)
        print(f"Final zone: {final_zone.type if final_zone else 'none'}")

        # ✅ monter automatiquement si on traverse une zone interdite
        safe = crossed_forbidden or current_z < self.safe_height
        print(f"Safe move: {safe}")

        # 🔁 Déplacement principal (z = safe_z si nécessaire)
        self.fb.move(
            x=x,
            y=y,
            z=self.safe_height if z is not None and not (final_zone and final_zone.type != "allowed") else z,
            safe_z=not safe
        )

        # ❌ Ne pas redescendre si la zone est interdite
        z_descended = False
        if z is not None and (final_zone is None or final_zone.type == "allowed"):
            if await self.wait_until_idle():
                self.fb.move(x=None, y=None, z=z)
                z_descended = True

        return {
            "status": "moved",
            "z_descended": z_descended,
            "final_zone": final_zone.type if final_zone else "none",
            "crossed_forbidden": crossed_forbidden
        }


    def goto_home(self):
        return self.fb.find_home()
        # Endpoint : https://my.farm.bot/api/device/find_home


    @lru_cache
    def garden_size(self):
        return self.fb.garden_size()
    
    def toast(self, message):
        return self.fb.toast(message)
    
    def lock(self):
        self.stop = True
        self.fb.e_stop()
        print("Stopping FarmBot")
        
    def unlock(self):
        self.stop = False
        self.fb.unlock()
        print("Resuming FarmBot")
        
    def would_cross_forbidden_zone(self, x: float, y: float) -> bool:
        current = self.status_data.get("location_data", {}).get("position", {})
        x0 = current.get("x")
        y0 = current.get("y")

        if x0 is None or y0 is None:
            return False  # Si on ne connaît pas la position, on assume que c'est OK

        # On parcourt la trajectoire à pas régulier (ex: tous les 50 mm)
        steps = 20
        for i in range(steps + 1):
            xi = x0 + (x - x0) * i / steps
            yi = y0 + (y - y0) * i / steps

            zone = self.zone_manager.get_zone_at(xi, yi)
            if zone and zone.type == "forbidden":
                return True  # ❌ on traverse une zone interdite

        return False  # ✅ pas de zone interdite traversée

    
    def grid_travel(self, start_x=0, start_y=0, width=None, length=None, rows=None, columns=None, callback=None):
        garden_size = self.garden_size()
        max_x, max_y = garden_size['x'], garden_size['y']

        width = width or max_x
        length = length or max_y
        
        opposite_x = start_x + width if start_x + width <= max_x else max_x
        opposite_y = start_y + length if start_y + length <= max_y else max_y

        rows = rows or 3
        columns = columns or 3

        step_x = (opposite_x - start_x) // (columns - 1) if columns > 1 else 0
        step_y = (opposite_y - start_y) // (rows - 1) if rows > 1 else 0
        
        message = f"Grid travel: {rows}x{columns} grid, {step_x}x{step_y} steps, starting at ({start_x}, {start_y}), width {width}, length {length}"
        
        self.fb.send_message(message, message_type="info")

        for row in range(rows):
            y = start_y + row * step_y

            # Mouvement en zigzag
            x_range = range(columns) if row % 2 == 0 else range(columns - 1, -1, -1)

            for col in x_range:
                if self.stop:
                    print("Stopping grid travel")
                    return
                
                x = start_x + col * step_x

                try:
                    self.fb.move(x, y)

                    if callback:
                        callback()

                    time.sleep(1)

                except Exception as e:
                    print(f"Error moving to ({x}, {y}): {e}")
                    
    def get_logs(self):
        # Endpoint : https://my.farm.bot/api/logs
        return self.fb.api_get("logs")
    
    async def take_photo(self):
        images = self.fb.take_photo()
        await asyncio.sleep(5)
        try:
            images = self.fb.api_get("images")
            if not images:
                return {"error": "No images found"}
            latest = sorted(images, key=lambda img: img["created_at"], reverse=True)[0]
            return {"url": latest.get("attachment_url")}
        except Exception as e:
            return {"error": str(e)}
