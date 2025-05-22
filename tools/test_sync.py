import pytest
from sync_farmbot_basics import Point, tool_to_checksum, clean_payload
import tempfile
import json
import os

# === Point model tests ===

def test_point_checksum_consistency():
    point_data = {
        "name": "My Point",
        "x": 100, "y": 200, "z": 300,
        "pointer_type": "GenericPointer",
        "meta": {"tag": "demo"},
        "radius": 10,
        "pullout_direction": 1,
        "plant_stage": "planned",
        "id": 123
    }

    p1 = Point.from_dict(point_data)
    p2 = Point.from_dict(point_data)
    assert p1.to_checksum() == p2.to_checksum()

    # Change a field
    point_data["x"] = 101
    p3 = Point.from_dict(point_data)
    assert p1.to_checksum() != p3.to_checksum()


def test_point_payload_output():
    data = {
        "name": "test",
        "x": 1, "y": 2, "z": 3,
        "pointer_type": "ToolSlot"
    }
    p = Point.from_dict(data)
    payload = p.to_post_payload()
    assert payload["pointer_type"] == "ToolSlot"
    assert "id" not in payload


# === Tool checksum test ===

def test_tool_checksum_uniqueness():
    tool1 = {"name": "Seeder", "status": None, "slot_id": 2, "x": 10, "y": 20, "z": 30, "meta": None}
    tool2 = {"name": "Seeder", "status": None, "slot_id": 2, "x": 10, "y": 21, "z": 30, "meta": None}
    assert tool_to_checksum(tool1) != tool_to_checksum(tool2)


# === Clean payload test ===

def test_clean_payload_removes_fields():
    raw = {
        "id": 123,
        "name": "test",
        "created_at": "today",
        "uuid": "abcd",
        "updated_at": "never"
    }
    cleaned = clean_payload(raw)
    for key in ["id", "created_at", "updated_at", "uuid"]:
        assert key not in cleaned


# === Checksum storage test ===

def test_checksum_save_and_load(tmp_path):
    from sync_farmbot_basics import save_synced_checksums, load_synced_checksums

    data = {
        "Tool": {"abc": 1},
        "ToolSlot": {"xyz": 2}
    }

    path = tmp_path / "checksums.json"
    original_file = "synced_resources.json"
    try:
        # Redirect global variable
        from sync_farmbot_basics import SYNCED_RESOURCES_FILE
        globals()["SYNCED_RESOURCES_FILE"] = str(path)

        save_synced_checksums(data)
        loaded = load_synced_checksums()
        assert loaded == data
    finally:
        # Reset to original filename
        globals()["SYNCED_RESOURCES_FILE"] = original_file
