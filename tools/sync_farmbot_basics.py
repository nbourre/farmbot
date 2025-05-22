import json
import os
import datetime
import argparse
from farmbot import Farmbot
from auth import load_token
from copy import deepcopy
from dataclasses import dataclass
from typing import Optional, Dict, Any
import hashlib


SYNCED_RESOURCES_FILE = "synced_resources.json"

class SyncIndex:
    def __init__(self, path="synced_points.json"):
        self.path = path
        self.data = {"points": {}}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def has_point(self, original_id: int) -> bool:
        return str(original_id) in self.data["points"]

    def add_point(self, original_id: int, new_id: int):
        self.data["points"][str(original_id)] = new_id
        self._save()

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)


@dataclass
class Point:
    name: str
    x: float
    y: float
    z: float
    pointer_type: str = "GenericPointer"
    meta: Optional[Dict[str, Any]] = None
    radius: Optional[float] = None
    pullout_direction: Optional[int] = None
    plant_stage: Optional[str] = None
    original_id: Optional[int] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Point':
        return Point(
            name=data["name"],
            x=data["x"],
            y=data["y"],
            z=data["z"],
            pointer_type=data.get("pointer_type", "GenericPointer"),
            meta=data.get("meta"),
            radius=data.get("radius"),
            pullout_direction=data.get("pullout_direction"),
            plant_stage=data.get("plant_stage"),
            original_id=data.get("id")
        )

    def to_post_payload(self) -> Dict[str, Any]:
        payload = {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "pointer_type": self.pointer_type,
        }
        if self.meta is not None:
            payload["meta"] = self.meta
        if self.radius is not None:
            payload["radius"] = self.radius
        if self.pullout_direction is not None:
            payload["pullout_direction"] = self.pullout_direction
        if self.plant_stage is not None:
            payload["plant_stage"] = self.plant_stage
        return payload  

    def to_checksum(self) -> str:
        """Create a content-based checksum for deduplication."""
        data = {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "pointer_type": self.pointer_type,
            "meta": self.meta,
            "radius": self.radius,
            "pullout_direction": self.pullout_direction,
            "plant_stage": self.plant_stage,
        }
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()



# === Clean API Payload ===
def clean_payload(payload):
    for key in ["id", "created_at", "updated_at", "uuid"]:
        payload.pop(key, None)
    return payload

# === Count Resources ===
def count_resources(fb):
    points = fb.api_get("points")
    return {
        "tools": len(fb.api_get("tools")),
        "tool_slots": len([p for p in points if p["pointer_type"] == "ToolSlot"]),
        "points": len(points)
    }


# === Save Backup to JSON Files ===
def save_backup(name, data, folder):
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"{name}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ {name} backed up to {file_path}")

def backup_all(prod_fb):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder = os.path.join("backups", timestamp)
    print(f"\n📦 Backing up production FarmBot data to {folder}...")
    save_backup("tools", prod_fb.api_get("tools"), folder)
    all_points = prod_fb.api_get("points")
    save_backup("points", all_points, folder)
    tool_slots = [p for p in all_points if p["pointer_type"] == "ToolSlot"]
    save_backup("tool_slots", tool_slots, folder)


# === Sync Functions ===
def sync_tools(prod_fb, sim_fb, dry_run=False):

    tools = prod_fb.api_get("tools")
    synced = load_synced_checksums()
    already_synced = synced.get("Tool", {})

    created, updated, skipped = 0, 0, 0

    for tool in tools:
        checksum = tool_to_checksum(tool)
        payload = clean_payload(deepcopy(tool))

        if checksum in already_synced:
            remote_id = already_synced[checksum]
            if dry_run:
                print(f"[DRY-RUN] Would update Tool {tool.get('name')} → ID {remote_id}")
            else:
                sim_fb.api_put(f"tools/{remote_id}", payload)
            updated += 1
        else:
            if dry_run:
                print(f"[DRY-RUN] Would create Tool {tool.get('name')}")
                new_id = -1  # simulate
            else:
                response = sim_fb.api_post("tools", payload)
                new_id = response.get("id")
            already_synced[checksum] = new_id
            created += 1


    synced["Tool"] = already_synced
    if not dry_run:
        save_synced_checksums(synced)

    print(f"✅ Tools → Created: {created}, Updated: {updated}, Skipped: {skipped}")



def sync_tool_slots(prod_fb, sim_fb, dry_run=False):

    all_points = prod_fb.api_get("points")
    tool_slots = [Point.from_dict(p) for p in all_points if p.pointer_type == "ToolSlot"]

    synced = load_synced_checksums()
    already_synced = synced.get("ToolSlot", {})

    created, updated = 0, 0

    for slot in tool_slots:
        checksum = slot.to_checksum()
        payload = slot.to_post_payload()

        if checksum in already_synced:
            if dry_run:
                print(f"[DRY-RUN] Would update ToolSlot '{slot.name}' → ID {already_synced[checksum]}")
            else:
                sim_fb.api_put(f"points/{already_synced[checksum]}", payload)
            updated += 1
        else:
            if dry_run:
                print(f"[DRY-RUN] Would create ToolSlot '{slot.name}'")
                new_id = -1
            else:
                response = sim_fb.api_post("points", payload)
                new_id = response.get("id")
            already_synced[checksum] = new_id
            created += 1

    synced["ToolSlot"] = already_synced
    
    if not dry_run:
        save_synced_checksums(synced)
        
    print(f"✅ ToolSlots → Created: {created}, Updated: {updated}")

def sync_points_by_type(prod_fb, sim_fb, dry_run=False):

    raw_points = prod_fb.api_get("points")
    all_points = [Point.from_dict(p) for p in raw_points]
    types = sorted(set(p.pointer_type for p in all_points))

    synced = load_synced_checksums()

    print("\nSync Points by Type:")
    for idx, t in enumerate(types, start=1):
        print(f"{idx}. {t}")
    print(f"{len(types)+1}. All")
    print(f"{len(types)+2}. Cancel")

    try:
        choice = int(input("Select pointer_type to sync: ").strip())
        if choice == len(types) + 2:
            print("❌ Cancelled.")
            return
        elif choice == len(types) + 1:
            selected_types = types
        else:
            selected_types = [types[choice - 1]]
    except (ValueError, IndexError):
        print("Invalid choice. Aborting.")
        return

    total_created, total_updated = 0, 0

    for ptype in selected_types:
        already_synced = synced.get(ptype, {})
        to_sync = [p for p in all_points if p.pointer_type == ptype]

        created, updated = 0, 0

        for p in to_sync:
            checksum = p.to_checksum()
            payload = p.to_post_payload()

            if checksum in already_synced:
                if dry_run:
                    print(f"[DRY-RUN] Would update {ptype} point '{p.name}' → ID {already_synced[checksum]}")
                else:
                    sim_fb.api_put(f"points/{already_synced[checksum]}", payload)
                updated += 1
            else:
                if dry_run:
                    print(f"[DRY-RUN] Would create {ptype} point '{p.name}'")
                    new_id = -1
                else:
                    response = sim_fb.api_post("points", payload)
                    new_id = response.get("id")
                already_synced[checksum] = new_id
                created += 1


        synced[ptype] = already_synced
        total_created += created
        total_updated += updated
        print(f"🔄 {ptype} → Created: {created}, Updated: {updated}")

    if not dry_run:
        save_synced_checksums(synced)
        
    print(f"✅ All selected point types synced. Total created: {total_created}, updated: {total_updated}")


def sync_points(prod_fb, sim_fb):
    points = prod_fb.api_get("points")
    print(f"Syncing {len(points)} points...")
    for point in points:
        sim_fb.post("points", clean_payload(deepcopy(point)))


def load_synced_checksums() -> Dict[str, Dict[str, int]]:
    if not os.path.exists(SYNCED_RESOURCES_FILE):
        return {}
    with open(SYNCED_RESOURCES_FILE, "r") as f:
        return json.load(f)

def save_synced_checksums(synced: Dict[str, Dict[str, int]]):
    with open(SYNCED_RESOURCES_FILE, "w") as f:
        json.dump(synced, f, indent=2)

def tool_to_checksum(tool: Dict[str, Any]) -> str:
    data = {
        "name": tool.get("name"),
        "status": tool.get("status"),
        "slot": tool.get("slot_id"),
        "pullout_direction": tool.get("pullout_direction"),
        "x": tool.get("x"),
        "y": tool.get("y"),
        "z": tool.get("z"),
        "meta": tool.get("meta"),
    }
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


# === Display Comparison ===
def show_comparison(prod_counts, sim_counts):
    print("\n🧮 Resource Counts:")
    print(f"{'Resource':<12} | {'Production':>10} | {'Simulator':>10}")
    print("-" * 38)
    for key in prod_counts:
        print(f"{key:<12} | {prod_counts[key]:>10} | {sim_counts[key]:>10}")
    print("-" * 38)

def print_menu():
    print("\n=== FarmBot Sync Menu ===")
    print("1. Sync Tools")
    print("2. Sync Tool Slots")
    print("3. Sync Points")
    print("4. Sync All")
    print("5. View Resource Counts")
    print("6. Sync Points by Type")
    print("0. Exit")

def confirm():
    answer = input("Proceed with sync? [y/N]: ").strip().lower()
    return answer in ["y", "yes"]

# === Main ===
def main():
    parser = argparse.ArgumentParser(description="FarmBot Sync Tool")
    parser.add_argument("--backup-only", action="store_true", help="Only backup production FarmBot data")
    parser.add_argument("--reset-synced", action="store_true", help="Clear synced resource checksum cache")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync actions without applying changes")

    args = parser.parse_args()

    # Load tokens
    prod_token = load_token("farmbot_authorization_token_prod.json")
    sim_token = load_token("farmbot_authorization_token.json")
    

    # Instantiate and configure Farmbot clients
    prod_fb = Farmbot()
    prod_fb.set_token(prod_token)

    sim_fb = Farmbot()
    sim_fb.set_token(sim_token)

    if args.backup_only:
        backup_all(prod_fb)
        return

    if args.reset_synced and os.path.exists(SYNCED_RESOURCES_FILE):
        os.remove(SYNCED_RESOURCES_FILE)
        print("🧹 Synced resource cache cleared.")


    while True:
        print_menu()
        choice = input("Enter your choice [1-7]: ").strip()

        if choice in {"1", "2", "3", "4", "6"}:
            prod_counts = count_resources(prod_fb)
            sim_counts = count_resources(sim_fb)
            show_comparison(prod_counts, sim_counts)

            backup_all(prod_fb)

            if not confirm():
                print("❌ Sync cancelled.")
                continue

            if choice == "1":
                sync_tools(prod_fb, sim_fb, args.dry_run)
            elif choice == "2":
                sync_tool_slots(prod_fb, sim_fb, args.dry_run)
            elif choice == "3":
                sync_points(prod_fb, sim_fb, args.dry_run)
            elif choice == "4":
                sync_tools(prod_fb, sim_fb, args.dry_run)
                sync_tool_slots(prod_fb, sim_fb, args.dry_run)
                sync_points(prod_fb, sim_fb, args.dry_run)
            elif choice == "6":
                sync_points_by_type(prod_fb, sim_fb, args.dry_run)


        elif choice == "5":
            prod_counts = count_resources(prod_fb)
            sim_counts = count_resources(sim_fb)
            show_comparison(prod_counts, sim_counts)

        elif choice == "0":
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()
