"""Main agent orchestrator for Jira-ServiceNow sync."""

import time
from typing import List, Optional
from datetime import datetime
from src.config import AppConfig
from src.jira_client import JiraClient
from src.servicenow_client import ServiceNowClient
from src.state_manager import StateManager
from src.models import JiraStory, SyncResult, UpdateSet
from src.logger import LoggerMixin, setup_logging
from src.utils import (
    generate_parent_name,
    generate_child_name,
    sanitize_name,
    format_duration
)


class JiraServiceNowAgent(LoggerMixin):
    """Main agent for syncing Jira stories to ServiceNow update sets."""

    def __init__(self, config: AppConfig):
        """Initialize the agent.

        Args:
            config: Application configuration
        """
        self.config = config
        self.jira_client = JiraClient(config.jira)
        self.servicenow_client = ServiceNowClient(config.servicenow)
        self.state_manager = StateManager(config.agent.state_file_path)
        self.logger = setup_logging(config.agent)

    def run_once(self, dry_run: bool = False) -> SyncResult:
        """Run a single sync cycle.

        Args:
            dry_run: If True, don't make actual changes

        Returns:
            SyncResult with details
        """
        self.logger.info(f"Starting agent | agent_name={self.config.agent.name}")
        if dry_run:
            self.logger.warning("Running in DRY RUN mode - no changes will be made")

        result = SyncResult()
        start_time = datetime.utcnow()

        try:
            # Fetch stories from Jira
            stories = self.jira_client.fetch_stories()
            result.total_stories = len(stories)
            self.logger.info(f"Fetched {len(stories)} stories from Jira")

            if not stories:
                self.logger.warning("No stories found to process")
                result.success = True
                return self._finalize_result(result, start_time)

            # Process each story
            for story in stories:
                try:
                    self._process_story(story, result, dry_run)
                except Exception as e:
                    self.logger.error(f"Error processing story {story.key}: {e}")
                    result.failed_count += 1
                    result.failed_stories.append({
                        'key': story.key,
                        'error': str(e)
                    })

            result.success = result.failed_count == 0
            self.logger.info(f"Sync cycle completed | synced={result.synced_count} | failed={result.failed_count}")

        except Exception as e:
            self.logger.error(f"Fatal error during sync: {e}")
            result.success = False
            result.errors.append(str(e))
            self.state_manager.record_sync_failure(str(e))
            return self._finalize_result(result, start_time)

        # Update state
        if result.success:
            self.state_manager.record_sync_success()
        else:
            self.state_manager.record_sync_failure(f"{result.failed_count} stories failed")

        return self._finalize_result(result, start_time)

    def _process_story(self, story: JiraStory, result: SyncResult, dry_run: bool = False):
        """Process a single Jira story.

        Args:
            story: JiraStory object
            result: SyncResult to update
            dry_run: If True, don't make actual changes
        """
        # Skip if already processed
        if self.state_manager.is_story_processed(story.key):
            self.logger.info(f"Skipping already processed story | key={story.key}")
            result.skipped_count += 1
            return

        # Skip if no update sets
        if not story.update_sets:
            self.logger.debug(f"Story has no update sets | key={story.key}")
            result.skipped_count += 1
            return

        self.logger.info(
            f"Processing story | key={story.key} | update_sets={len(story.update_sets)}"
        )

        # Generate parent name
        parent_name = generate_parent_name(story.key, story.summary)

        # Check if parent already exists
        existing_parent = self.servicenow_client.get_update_set(parent_name)
        if existing_parent:
            parent_sys_id = existing_parent.get('sys_id')
            self.logger.info(f"Parent already exists | sys_id={parent_sys_id}")
        else:
            # Create parent with children
            parent_sys_id = self.servicenow_client.create_parent_with_children(
                parent_name=parent_name,
                child_names=story.update_sets,
                jira_story_key=story.key,
                dry_run=dry_run
            )

        if parent_sys_id:
            self.state_manager.mark_story_processed(story.key)
            self.state_manager.add_update_set_mapping(story.key, parent_sys_id)
            result.synced_count += 1
            result.created_update_sets.append(parent_sys_id)
            self.logger.info(f"Successfully synced story | key={story.key} | parent_sys_id={parent_sys_id}")
        else:
            result.failed_count += 1
            result.failed_stories.append({
                'key': story.key,
                'error': 'Failed to create parent update set'
            })

    def _finalize_result(self, result: SyncResult, start_time: datetime) -> SyncResult:
        """Finalize sync result with timing and summary.

        Args:
            result: SyncResult object
            start_time: Sync start time

        Returns:
            Updated SyncResult
        """
        result.completed_at = datetime.utcnow()
        result.duration_seconds = (result.completed_at - start_time).total_seconds()

        self.logger.info(
            f"Agent completed | success={result.success} | "
            f"total={result.total_stories} | synced={result.synced_count} | "
            f"failed={result.failed_count} | skipped={result.skipped_count} | "
            f"duration={format_duration(result.duration_seconds)}"
        )

        return result

    def cleanup(self):
        """Clean up resources."""
        self.jira_client.close()
        self.servicenow_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
