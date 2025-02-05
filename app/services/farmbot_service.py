from farmbot import Farmbot
from app.utils.auth import load_token

class FarmBotService:
    def __init__(self):
        self.fb = Farmbot()
        self.token = load_token()
        self.fb.set_token(self.token)

    def get_status(self):
        return self.fb.api_get("device") # Retrieves FarmBot device status

    def move(self, x, y, z):
        self.fb.send_message("move_absolute", {"x": x, "y": y, "z": z})
        return {"status": "Moving", "position": {"x": x, "y": y, "z": z}}

    def garden_size(self):
        return self.fb.garden_size()
    
    def toast(self, message):
        return self.fb.toast(message)
    