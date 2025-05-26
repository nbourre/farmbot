import json
from typing import List, Optional


class Zone:
    def __init__(self, id: str, name: str, x1: float, y1: float, x2: float, y2: float, type: str):
        self.id = id
        self.name = name
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)
        self.type = type  # "allowed", "forbidden", or "admin_only"

    def contains(self, x: float, y: float) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "type": self.type,
        }

    @staticmethod
    def from_dict(data: dict):
        return Zone(
            id=data["id"],
            name=data["name"],
            x1=data["x1"],
            y1=data["y1"],
            x2=data["x2"],
            y2=data["y2"],
            type=data["type"]
        )


class ZoneManager:
    def __init__(self, zones: Optional[List[Zone]] = None):
        self.zones = zones or []

    def add_zone(self, zone: Zone):
        self.zones.append(zone)

    def get_zone_at(self, x: float, y: float) -> Optional[Zone]:
        for zone in self.zones:
            if zone.contains(x, y):
                return zone
        return None

    def is_operation_allowed(self, x: float, y: float, z: float, action_type: str, safe_z: float) -> bool:
        zone = self.get_zone_at(x, y)
        if zone is None or zone.type == "allowed":
            return True

        if zone.type == "forbidden":
            if action_type in ("take_photo", "scan", "move"):
                return True
            if z > safe_z:
                return True
            return False
        
        if zone.type == "admin_only":
            return False  # Could be extended to check permissions
        
        return True

    def load_from_file(self, path: str):
        with open(path, "r") as f:
            data = json.load(f)
            self.zones = [Zone.from_dict(z) for z in data]

    def save_to_file(self, path: str):
        with open(path, "w") as f:
            json.dump([z.to_dict() for z in self.zones], f, indent=2)
            
    # Get all zones as a list of dictionaries
    def get_all_zones(self) -> List[dict]:
        return [zone.to_dict() for zone in self.zones]
