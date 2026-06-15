"""State management for tracking processed items and sync history."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from src.models import AgentState
from src.logger import LoggerMixin


class StateManager(LoggerMixin):
    """Manages agent state persistence."""

    def __init__(self, state_file_path: str):
        """Initialize state manager.

        Args:
            state_file_path: Path to state file
        """
        self.state_file_path = Path(state_file_path)
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> AgentState:
        """Load state from file.

        Returns:
            AgentState object
        """
        if self.state_file_path.exists():
            try:
                with open(self.state_file_path, 'r') as f:
                    data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    if data.get('last_sync_time'):
                        data['last_sync_time'] = datetime.fromisoformat(data['last_sync_time'])
                    if data.get('last_error_time'):
                        data['last_error_time'] = datetime.fromisoformat(data['last_error_time'])
                    return AgentState(**data)
            except Exception as e:
                self.logger.warning(f"Failed to load state file: {e}. Starting fresh.")
                return AgentState()
        return AgentState()

    def save_state(self):
        """Save current state to file."""
        try:
            state_dict = self.state.dict()
            # Convert datetime objects to strings for JSON serialization
            if state_dict.get('last_sync_time'):
                state_dict['last_sync_time'] = state_dict['last_sync_time'].isoformat()
            if state_dict.get('last_error_time'):
                state_dict['last_error_time'] = state_dict['last_error_time'].isoformat()

            with open(self.state_file_path, 'w') as f:
                json.dump(state_dict, f, indent=2)
            self.logger.debug(f"State saved to {self.state_file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def mark_story_processed(self, story_key: str):
        """Mark a story as processed.

        Args:
            story_key: Jira story key
        """
        if story_key not in self.state.processed_stories:
            self.state.processed_stories.append(story_key)
        self.save_state()

    def is_story_processed(self, story_key: str) -> bool:
        """Check if story was already processed.

        Args:
            story_key: Jira story key

        Returns:
            True if processed
        """
        return story_key in self.state.processed_stories

    def add_update_set_mapping(self, jira_key: str, servicenow_sys_id: str):
        """Record mapping between Jira story and ServiceNow update set.

        Args:
            jira_key: Jira story key
            servicenow_sys_id: ServiceNow sys_id
        """
        if jira_key not in self.state.created_update_sets:
            self.state.created_update_sets[jira_key] = servicenow_sys_id
        self.save_state()

    def get_update_set_mapping(self, jira_key: str) -> Optional[str]:
        """Get ServiceNow sys_id for a Jira story.

        Args:
            jira_key: Jira story key

        Returns:
            ServiceNow sys_id or None
        """
        return self.state.created_update_sets.get(jira_key)

    def set_last_parent(self, parent_sys_id: str):
        """Set the last created parent update set.

        Args:
            parent_sys_id: Parent sys_id
        """
        self.state.last_parent_created = parent_sys_id
        self.save_state()

    def update_sync_time(self):
        """Update last sync timestamp."""
        self.state.last_sync_time = datetime.utcnow()
        self.save_state()

    def record_sync_success(self):
        """Record a successful sync."""
        self.state.successful_syncs += 1
        self.state.error_count = 0
        self.state.last_error = None
        self.update_sync_time()

    def record_sync_failure(self, error: str):
        """Record a failed sync.

        Args:
            error: Error message
        """
        self.state.failed_syncs += 1
        self.state.error_count += 1
        self.state.last_error = error
        self.state.last_error_time = datetime.utcnow()
        self.update_sync_time()

    def reset(self):
        """Reset state to initial values."""
        self.state = AgentState()
        self.save_state()
        self.logger.info("State reset")

    def get_summary(self) -> str:
        """Get a summary of the current state.

        Returns:
            Summary string
        """
        return (
            f"State Summary:\n"
            f"  Last Sync: {self.state.last_sync_time}\n"
            f"  Last Parent: {self.state.last_parent_created}\n"
            f"  Processed Stories: {len(self.state.processed_stories)}\n"
            f"  Created Update Sets: {len(self.state.created_update_sets)}\n"
            f"  Successful Syncs: {self.state.successful_syncs}\n"
            f"  Failed Syncs: {self.state.failed_syncs}\n"
            f"  Error Count: {self.state.error_count}\n"
            f"  Last Error: {self.state.last_error}"
        )
