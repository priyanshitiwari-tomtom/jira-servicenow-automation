"""Utility functions for the agent."""

import re
from typing import List, Optional
from datetime import datetime, timedelta


def sanitize_name(name: str) -> str:
    """Sanitize a string to be a valid ServiceNow update set name.

    Args:
        name: Original name

    Returns:
        Sanitized name
    """
    # Remove special characters, keep alphanumeric and underscores
    sanitized = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces with underscores
    sanitized = re.sub(r'\s+', '_', sanitized)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Convert to lowercase
    sanitized = sanitized.lower()
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized


def generate_parent_deployment_name(sprint_name: Optional[str] = None) -> str:
    """Generate a parent deployment update set name.

    Naming format: DEPLOYMENT-{SPRINT}-{DATE}
    Example: DEPLOYMENT-SPRINT-12-2024-06-15

    Args:
        sprint_name: Jira sprint name

    Returns:
        Parent update set name
    """
    date_str = datetime.now().strftime('%Y-%m-%d')

    if sprint_name:
        sprint_part = sanitize_name(sprint_name)
        parent_name = f"DEPLOYMENT-{sprint_part}-{date_str}"
    else:
        parent_name = f"DEPLOYMENT-{date_str}"

    return parent_name


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def is_thursday() -> bool:
    """Check if today is Thursday.

    Returns:
        True if today is Thursday (weekday 3)
    """
    return datetime.now().weekday() == 3


def is_time_within_window(target_hour: int, target_minute: int, window_minutes: int = 5) -> bool:
    """Check if current time is within a window of target time.

    Args:
        target_hour: Target hour (0-23)
        target_minute: Target minute (0-59)
        window_minutes: Window tolerance in minutes

    Returns:
        True if within window
    """
    now = datetime.now()
    target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    delta = abs((now - target_time).total_seconds()) / 60
    return delta <= window_minutes
