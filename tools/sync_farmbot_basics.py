import json
import os
import datetime
import argparse
from farmbot import Farmbot
from auth import load_token
from copy import deepcopy


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
def sync_tools(prod_fb, sim_fb):
    tools = prod_fb.api_get("tools")["tools"]
    print(f"Syncing {len(tools)} tools...")
    for tool in tools:
        sim_fb.post("tools", clean_payload(deepcopy(tool)))

def sync_tool_slots(prod_fb, sim_fb):
    all_points = prod_fb.api_get("points")
    tool_slots = [p for p in all_points if p["pointer_type"] == "ToolSlot"]
    print(f"Syncing {len(tool_slots)} tool slots...")
    for slot in tool_slots:
        sim_fb.api_post("points", clean_payload(deepcopy(slot)))


def sync_points(prod_fb, sim_fb):
    points = prod_fb.api_get("points")
    print(f"Syncing {len(points)} points...")
    for point in points:
        sim_fb.post("points", clean_payload(deepcopy(point)))

# === Display Comparison ===
def show_comparison(prod_counts, sim_counts):
    print("\n🧮 Resource Counts:")
    print(f"{'Resource':<12} | {'Production':>10} | {'Simulator':>10}")
    print("-" * 38)
    for key in prod_counts:
        print(f"{key:<12} | {prod_counts[key]:>10} | {sim_counts[key]:>10}")
    print("-" * 38)

# === User Menu ===
def print_menu():
    print("\n=== FarmBot Sync Menu ===")
    print("1. Sync Tools")
    print("2. Sync Tool Slots")
    print("3. Sync Points")
    print("4. Sync All")
    print("5. Exit")
    print("6. View Resource Counts")

def confirm():
    answer = input("Proceed with sync? [y/N]: ").strip().lower()
    return answer in ["y", "yes"]

# === Main ===
def main():
    parser = argparse.ArgumentParser(description="FarmBot Sync Tool")
    parser.add_argument("--backup-only", action="store_true", help="Only backup production FarmBot data")
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

    while True:
        print_menu()
        choice = input("Enter your choice [1-6]: ").strip()

        if choice in {"1", "2", "3", "4"}:
            prod_counts = count_resources(prod_fb)
            sim_counts = count_resources(sim_fb)
            show_comparison(prod_counts, sim_counts)

            backup_all(prod_fb)

            if not confirm():
                print("❌ Sync cancelled.")
                continue

            if choice == "1":
                sync_tools(prod_fb, sim_fb)
            elif choice == "2":
                sync_tool_slots(prod_fb, sim_fb)
            elif choice == "3":
                sync_points(prod_fb, sim_fb)
            elif choice == "4":
                sync_tools(prod_fb, sim_fb)
                sync_tool_slots(prod_fb, sim_fb)
                sync_points(prod_fb, sim_fb)

        elif choice == "5":
            print("Exiting. Goodbye!")
            break

        elif choice == "6":
            prod_counts = count_resources(prod_fb)
            sim_counts = count_resources(sim_fb)
            show_comparison(prod_counts, sim_counts)

        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()
