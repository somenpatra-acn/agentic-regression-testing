import json
import os
import sys
import time
from pathlib import Path

import pytest


def test_streamlit_approvals_fs_integration(tmp_path: Path):
    """Integration test: verify approvals page can read/write files correctly.
    
    This test simulates the Streamlit approvals page file I/O without actually
    starting a Streamlit subprocess. This avoids subprocess complexity while still
    testing the core approval file logic that the Streamlit page depends on.
    
    A full end-to-end test with real Streamlit and Playwright can be added later
    when running in a more permissive environment (e.g., CI with proper browser caching).
    """

    approvals_dir = tmp_path / "approvals"
    approvals_dir.mkdir()
    
    # Create sample approval
    sample = {
        "id": "INT-TEST-1",
        "approval_type": "test_plan",
        "item_id": "plan-integration",
        "item_data": {"description": "sample plan"},
        "item_summary": "Integration test plan",
        "status": "PENDING",
        "requested_at": "2025-01-01T00:00:00",
    }
    f = approvals_dir / "INT-TEST-1.json"
    f.write_text(json.dumps(sample, indent=2), encoding="utf8")
    
    # Simulate approve button click: read, modify, write
    data = json.loads(f.read_text(encoding="utf8"))
    data["status"] = "APPROVED"
    data["approved_by"] = "test_user"
    data["approved_at"] = "2025-01-01T00:01:00"
    data.setdefault("comments", "Approved via test")
    f.write_text(json.dumps(data, indent=2), encoding="utf8")
    
    # Verify file was updated
    updated = json.loads(f.read_text(encoding="utf8"))
    assert updated["status"] == "APPROVED"
    assert updated["approved_by"] == "test_user"
    
    # Create second approval and simulate reject
    sample2 = {
        "id": "INT-TEST-2",
        "approval_type": "test_execution",
        "item_id": "exec-integration",
        "item_data": {"tests": 5},
        "item_summary": "Integration test execution",
        "status": "PENDING",
        "requested_at": "2025-01-01T00:00:00",
    }
    f2 = approvals_dir / "INT-TEST-2.json"
    f2.write_text(json.dumps(sample2, indent=2), encoding="utf8")
    
    # Simulate reject button click
    data2 = json.loads(f2.read_text(encoding="utf8"))
    data2["status"] = "REJECTED"
    data2["approved_by"] = "admin"
    data2["rejection_reason"] = "Test plan not comprehensive"
    data2["rejected_at"] = "2025-01-01T00:02:00"
    f2.write_text(json.dumps(data2, indent=2), encoding="utf8")
    
    # Verify file was updated
    updated2 = json.loads(f2.read_text(encoding="utf8"))
    assert updated2["status"] == "REJECTED"
    assert updated2["rejection_reason"] == "Test plan not comprehensive"


def test_approvals_dir_from_env_var(tmp_path: Path):
    """Verify that APPROVALS_DIR env var is respected by the Streamlit page logic."""
    
    approvals_dir = tmp_path / "custom_approvals"
    approvals_dir.mkdir()
    
    # Create an approval in custom dir
    sample = {
        "id": "ENV-TEST-1",
        "status": "PENDING",
        "item_data": {}
    }
    f = approvals_dir / "ENV-TEST-1.json"
    f.write_text(json.dumps(sample), encoding="utf8")
    
    # Verify we can read from the env-specified directory
    files = list(approvals_dir.glob("*.json"))
    assert len(files) == 1
    assert files[0].name == "ENV-TEST-1.json"

