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


def generate_parent_name(story_key: str, story_summary: str) -> str:
    """Generate a parent update set name from story info.

    Args:
        story_key: Jira story key
        story_summary: Story summary

    Returns:
        Parent update set name
    """
    # Use story key and first few words of summary
    summary_words = story_summary.split()[:3]
    summary_part = '_'.join(summary_words)
    parent_name = f"parent_{story_key}_{summary_part}"
    return sanitize_name(parent_name)


def generate_child_name(update_set_name: str, parent_key: str) -> str:
    """Generate a child update set name.

    Args:
        update_set_name: Original update set name
        parent_key: Parent story key

    Returns:
        Child update set name
    """
    child_name = f"child_{parent_key}_{update_set_name}"
    return sanitize_name(child_name)


def parse_update_set_reference(text: str) -> List[str]:
    """Parse update set references from text.

    Supports patterns like:
    - UpdateSet: ABC123
    - Update Set - XYZ789
    - us_ABC_123

    Args:
        text: Text to parse

    Returns:
        List of update set references
    """
    if not text:
        return []

    update_sets = []

    # Pattern 1: "UpdateSet: ABC123" or "Update Set: XYZ"
    pattern1 = r'[Uu]pdate[\s-]*[Ss]et[:\s]+([\w-]+)'
    matches = re.findall(pattern1, text)
    update_sets.extend(matches)

    # Pattern 2: "us_ABC_123" or similar
    pattern2 = r'(us_[\w]+)'
    matches = re.findall(pattern2, text)
    update_sets.extend(matches)

    # Remove duplicates and empty values
    update_sets = list(set(s.strip() for s in update_sets if s.strip()))
    return update_sets


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


def is_recent(timestamp: datetime, days: int = 7) -> bool:
    """Check if timestamp is within recent days.

    Args:
        timestamp: Datetime to check
        days: Number of days to consider recent

    Returns:
        True if recent
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    return timestamp > cutoff if timestamp else False


def batch_list(items: List, batch_size: int) -> List[List]:
    """Split list into batches.

    Args:
        items: List to batch
        batch_size: Size of each batch

    Returns:
        List of batches
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
