from farmbot import Farmbot
from app.utils.auth import load_token
import time
from functools import lru_cache

class FarmBotService:
    def __init__(self):
        self.fb = Farmbot()
        self.token = load_token()
        self.fb.set_token(self.token)

    def get_status(self):
        return self.fb.api_get("device") # Retrieves FarmBot device status

    def move(self, x=None, y=None, z=None):
        self.fb.move(x, y, z, safe_z=True);
        return {"status": "Moving", "position": {"x": x, "y": y, "z": z}}

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
    
    def grid_travel(self, start_x=0, start_y=0, width=None, length=None, rows=None, columns=None, callback=None):
        garden_size = self.garden_size()
        max_x, max_y = garden_size['x'], garden_size['y']

        width = width or max_x
        length = length or max_y

        rows = rows or 3
        columns = columns or 3

        step_x = (width - start_x) // (columns - 1) if columns > 1 else 0
        step_y = (length - start_y) // (rows - 1) if rows > 1 else 0

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
