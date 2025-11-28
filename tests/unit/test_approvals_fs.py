import json
from pathlib import Path
from datetime import datetime


def _create_sample(tmp_path: Path):
    approvals_dir = tmp_path / "approvals"
    approvals_dir.mkdir()
    sample = {
        "id": "TEST-APPROVAL-1",
        "approval_type": "test_plan",
        "item_id": "plan-demo",
        "item_data": {"foo": "bar"},
        "item_summary": "Sample test plan",
        "status": "PENDING",
        "requested_at": datetime.utcnow().isoformat(),
    }
    f = approvals_dir / "TEST-APPROVAL-1.json"
    f.write_text(json.dumps(sample))
    return f, sample


def test_approve_writes_fields(tmp_path: Path):
    """Simulate approving an approval JSON and verify fields are written."""
    f, _ = _create_sample(tmp_path)

    # Read, modify to APPROVED and write
    data = json.loads(f.read_text(encoding="utf8"))
    data["status"] = "APPROVED"
    data["approved_by"] = "tester"
    data["approved_at"] = datetime.utcnow().isoformat()
    data["comments"] = "Approved via unit test"
    f.write_text(json.dumps(data), encoding="utf8")

    # Read back and assert
    data2 = json.loads(f.read_text(encoding="utf8"))
    assert data2["status"] == "APPROVED"
    assert data2["approved_by"] == "tester"
    assert "approved_at" in data2
    assert data2["comments"] == "Approved via unit test"


def test_reject_writes_fields(tmp_path: Path):
    """Simulate rejecting an approval JSON and verify rejection fields."""
    f, _ = _create_sample(tmp_path)

    data = json.loads(f.read_text(encoding="utf8"))
    data["status"] = "REJECTED"
    data["approved_by"] = "admin"
    data["rejection_reason"] = "Invalid plan"
    data["rejected_at"] = datetime.utcnow().isoformat()
    f.write_text(json.dumps(data), encoding="utf8")

    data2 = json.loads(f.read_text(encoding="utf8"))
    assert data2["status"] == "REJECTED"
    assert data2["rejection_reason"] == "Invalid plan"


def test_edit_json_roundtrip(tmp_path: Path):
    """Edit the raw JSON and ensure it remains valid and changes persist."""
    f, _ = _create_sample(tmp_path)

    data = json.loads(f.read_text(encoding="utf8"))
    data["item_data"]["new_field"] = "value"
    f.write_text(json.dumps(data, indent=2), encoding="utf8")

    parsed = json.loads(f.read_text(encoding="utf8"))
    assert parsed["item_data"]["new_field"] == "value"
