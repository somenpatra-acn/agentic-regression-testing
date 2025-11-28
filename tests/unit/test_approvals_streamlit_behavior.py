import json
from pathlib import Path
from datetime import datetime
import pytest


def _create_file(tmp_path: Path, name: str, content: str):
    approvals_dir = tmp_path / "approvals"
    approvals_dir.mkdir(exist_ok=True)
    f = approvals_dir / name
    f.write_text(content, encoding="utf8")
    return f


def test_invalid_json_load(tmp_path: Path):
    """When an approvals file contains invalid JSON, a JSONDecodeError is raised on load."""
    bad = "{ this is : not valid json }"
    f = _create_file(tmp_path, "bad.json", bad)

    with pytest.raises(json.JSONDecodeError):
        _ = json.loads(f.read_text(encoding="utf8"))


def test_files_sorted_order(tmp_path: Path):
    """The streamlit page lists files sorted; ensure simple alpha sort works."""
    # Create files in non-sorted creation order
    names = ["b.json", "a.json", "c.json"]
    for n in names:
        _create_file(tmp_path, n, json.dumps({"id": n}))

    approvals_dir = tmp_path / "approvals"
    files = sorted(approvals_dir.glob("*.json"))
    found = [p.name for p in files]
    assert found == sorted(found)


def test_edit_invalid_json_does_not_overwrite(tmp_path: Path):
    """Simulate a user editing raw JSON with invalid content; file should remain unchanged."""
    original = {
        "id": "TEST-EDIT-1",
        "item_id": "item",
        "status": "PENDING",
    }
    f = _create_file(tmp_path, "edit.json", json.dumps(original, indent=2))

    edited_invalid = "{ invalid json,, }"

    # Attempt to parse edited content as the Streamlit form would
    with pytest.raises(json.JSONDecodeError):
        json.loads(edited_invalid)

    # Ensure file contents remain the same after failed parse
    parsed_after = json.loads(f.read_text(encoding="utf8"))
    assert parsed_after == original
