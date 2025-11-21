"""Helper utilities and common functions."""

import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    Load YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        Dictionary containing YAML data
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict[str, Any], file_path: str) -> None:
    """
    Save data to YAML file.

    Args:
        data: Data to save
        file_path: Path to save file
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary containing JSON data
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, file_path: str, indent: int = 2) -> None:
    """
    Save data to JSON file.

    Args:
        data: Data to save
        file_path: Path to save file
        indent: JSON indentation
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique identifier.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique identifier string
    """
    unique_id = str(uuid.uuid4())[:8].upper()
    if prefix:
        return f"{prefix}-{unique_id}"
    return unique_id


def generate_test_id() -> str:
    """Generate a unique test case ID."""
    return generate_id("TEST")


def generate_result_id() -> str:
    """Generate a unique test result ID."""
    return generate_id("RESULT")


def generate_approval_id() -> str:
    """Generate a unique approval ID."""
    return generate_id("APPROVAL")


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    return sanitized


def parse_env_var(value: str, default: Optional[str] = None) -> str:
    """
    Parse environment variable reference in format ${VAR_NAME}.

    Args:
        value: String potentially containing env var reference
        default: Default value if env var not found

    Returns:
        Resolved value
    """
    import os

    if not value:
        return default or ""

    pattern = r'\$\{([^}]+)\}'

    def replacer(match):
        var_name = match.group(1)
        return os.getenv(var_name, default or "")

    return re.sub(pattern, replacer, value)


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split list into chunks.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO format timestamp string."""
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))


def time_ago(dt: datetime) -> str:
    """
    Get human-readable time ago string.

    Args:
        dt: Datetime object

    Returns:
        Human-readable string like "2 hours ago"
    """
    now = datetime.utcnow()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=30):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d")


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def extract_error_message(exception: Exception) -> str:
    """
    Extract clean error message from exception.

    Args:
        exception: Exception object

    Returns:
        Clean error message
    """
    error_msg = str(exception)
    # Clean up common error prefixes
    error_msg = re.sub(r'^(Error|Exception):\s*', '', error_msg)
    return error_msg.strip()
