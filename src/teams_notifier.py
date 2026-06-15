"""Microsoft Teams integration for sending deployment reports."""

import requests
from typing import List, Optional, Dict, Any
from src.config import TeamsConfig
from src.models import SyncResult, StoryUpdateSetMapping
from src.logger import LoggerMixin


class TeamsNotifier(LoggerMixin):
    """Sends deployment reports to Microsoft Teams."""

    def __init__(self, config: TeamsConfig):
        """Initialize Teams notifier.

        Args:
            config: Teams configuration
        """
        self.config = config
        self.webhook_url = config.webhook_url

    def send_deployment_report(self, result: SyncResult) -> bool:
        """Send deployment report to Teams channel.

        Args:
            result: SyncResult with deployment details

        Returns:
            True if successful
        """
        try:
            payload = self._build_message(result)
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            self.logger.info(f"Deployment report sent to Teams | status_code={response.status_code}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send Teams message: {e}")
            return False

    def _build_message(self, result: SyncResult) -> Dict[str, Any]:
        """Build Teams message payload.

        Args:
            result: SyncResult

        Returns:
            Teams message payload
        """
        # Determine color based on success
        color = "28a745" if result.success else "dc3545"

        # Build summary section
        summary_facts = [
            {"name": "Status", "value": "✅ Success" if result.success else "❌ Failed"},
            {"name": "Total Stories", "value": str(result.total_stories)},
            {"name": "Synced", "value": str(result.synced_count)},
            {"name": "Failed", "value": str(result.failed_count)},
            {"name": "Skipped", "value": str(result.skipped_count)},
        ]

        if result.sprint_name:
            summary_facts.insert(0, {"name": "Sprint", "value": result.sprint_name})

        if result.parent_update_set_name:
            summary_facts.append({"name": "Parent Update Set", "value": result.parent_update_set_name})

        # Build story details section
        story_sections = self._build_story_details(result.story_mappings)

        # Main message card
        card = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": color,
            "summary": f"Deployment Report - {result.sprint_name or 'Ready for Deployment'}",
            "sections": [
                {
                    "activityTitle": f"📦 Deployment Report - {result.sprint_name or 'Ready for Deployment'}",
                    "facts": summary_facts,
                    "markdown": True
                }
            ] + story_sections
        }

        # Add potential action
        if result.parent_update_set_id:
            card["potentialAction"] = [
                {
                    "@type": "OpenUri",
                    "name": "View in ServiceNow",
                    "targets": [
                        {
                            "os": "default",
                            "uri": f"{self._get_servicenow_url()}/nav_to.do?uri=table/sn_chg_management_update_set.do?sys_id={result.parent_update_set_id}"
                        }
                    ]
                }
            ]

        return card

    def _build_story_details(self, mappings: List[StoryUpdateSetMapping]) -> List[Dict[str, Any]]:
        """Build story details sections.

        Args:
            mappings: List of story-to-updateset mappings

        Returns:
            List of Teams card sections
        """
        if not mappings:
            return []

        sections = []

        for mapping in mappings:
            facts = [
                {"name": "Story", "value": f"{mapping.story_key}: {mapping.story_summary}"},
                {"name": "Update Sets Count", "value": str(len(mapping.update_sets))},
            ]

            if mapping.assignee:
                facts.insert(1, {"name": "Assigned To", "value": mapping.assignee})

            if mapping.update_sets:
                facts.append({
                    "name": "Update Sets",
                    "value": "\n".join([f"• {us}" for us in mapping.update_sets])
                })

            sections.append({
                "activityTitle": f"📝 {mapping.story_key}",
                "facts": facts,
                "markdown": True
            })

        return sections

    def _get_servicenow_url(self) -> str:
        """Extract base URL from webhook URL or use config.

        Returns:
            ServiceNow instance URL
        """
        # This would typically come from config or be extracted from webhook
        # For now, return a placeholder
        return "https://your-instance.service-now.com"

    def send_error_notification(self, error_message: str, sprint_name: Optional[str] = None) -> bool:
        """Send error notification to Teams.

        Args:
            error_message: Error message
            sprint_name: Optional sprint name

        Returns:
            True if successful
        """
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "themeColor": "dc3545",
                "summary": "Deployment Agent Error",
                "sections": [
                    {
                        "activityTitle": f"❌ Deployment Agent Error - {sprint_name or 'Unknown Sprint'}",
                        "facts": [
                            {"name": "Error", "value": error_message}
                        ],
                        "markdown": True
                    }
                ]
            }

            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            self.logger.info("Error notification sent to Teams")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send error notification: {e}")
            return False
