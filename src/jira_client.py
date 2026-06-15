"""Jira API client for fetching stories and update sets."""

import requests
from typing import List, Optional
from datetime import datetime
from requests.auth import HTTPBasicAuth
from src.config import JiraConfig
from src.models import JiraStory
from src.logger import LoggerMixin


class JiraClient(LoggerMixin):
    """Client for interacting with Jira API."""

    def __init__(self, config: JiraConfig):
        """Initialize Jira client.

        Args:
            config: Jira configuration
        """
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.auth = HTTPBasicAuth(config.username, config.api_token)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({'Accept': 'application/json'})

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make API request to Jira.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response JSON

        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Jira API error: {e}")
            raise

    def fetch_stories(self, jql: Optional[str] = None) -> List[JiraStory]:
        """Fetch stories from Jira with update set information.

        Args:
            jql: Optional JQL query string

        Returns:
            List of JiraStory objects
        """
        if not jql:
            jql = f'project = "{self.config.project_key}" ORDER BY updated DESC'

        self.logger.info(f"Fetching stories from Jira | jql={jql}")

        stories = []
        start_at = 0
        max_results = 50

        while True:
            try:
                response = self._make_request(
                    'GET',
                    '/rest/api/3/search',
                    params={
                        'jql': jql,
                        'startAt': start_at,
                        'maxResults': max_results,
                        'expand': 'changelog',
                        'fields': 'summary,description,status,assignee,reporter,labels,created,updated'
                    }
                )

                for issue in response.get('issues', []):
                    story = self._parse_story(issue)
                    if story:
                        stories.append(story)

                total = response.get('total', 0)
                start_at += max_results

                if start_at >= total:
                    break

            except Exception as e:
                self.logger.error(f"Error fetching stories: {e}")
                break

        self.logger.info(f"Successfully fetched {len(stories)} stories")
        return stories

    def _parse_story(self, issue: dict) -> Optional[JiraStory]:
        """Parse Jira issue to JiraStory model.

        Args:
            issue: Jira issue data

        Returns:
            JiraStory object or None if parsing fails
        """
        try:
            fields = issue.get('fields', {})
            update_sets = self._extract_update_sets(fields)

            story = JiraStory(
                key=issue.get('key'),
                summary=fields.get('summary', ''),
                description=fields.get('description'),
                status=fields.get('status', {}).get('name', 'Unknown'),
                update_sets=update_sets,
                created=fields.get('created'),
                updated=fields.get('updated'),
                assignee=fields.get('assignee', {}).get('displayName'),
                reporter=fields.get('reporter', {}).get('displayName'),
                labels=fields.get('labels', []),
                custom_fields=fields
            )
            return story
        except Exception as e:
            self.logger.warning(f"Failed to parse story {issue.get('key')}: {e}")
            return None

    def _extract_update_sets(self, fields: dict) -> List[str]:
        """Extract update set names from issue fields.

        Args:
            fields: Issue fields dictionary

        Returns:
            List of update set names
        """
        update_sets = []

        # Check custom field
        field_value = fields.get(self.config.update_set_field)
        if field_value:
            if isinstance(field_value, str):
                # Single value
                update_sets.append(field_value.strip())
            elif isinstance(field_value, list):
                # Multiple values
                update_sets.extend([v.strip() for v in field_value if v])
            elif isinstance(field_value, dict) and 'value' in field_value:
                # Object with value
                update_sets.append(field_value['value'].strip())

        # Also check description for update set mentions
        description = fields.get('description', '')
        if description and isinstance(description, str):
            # Look for patterns like "UpdateSet: XYZ" in description
            import re
            matches = re.findall(r'[Uu]pdate[Ss]et[:\s]+([\w-]+)', description)
            update_sets.extend(matches)

        # Remove duplicates and empty values
        update_sets = list(set(s for s in update_sets if s))
        return update_sets

    def get_story(self, key: str) -> Optional[JiraStory]:
        """Get a specific story by key.

        Args:
            key: Jira issue key

        Returns:
            JiraStory object or None
        """
        try:
            response = self._make_request(
                'GET',
                f'/rest/api/3/issues/{key}',
                params={'fields': 'summary,description,status,assignee,reporter,labels,created,updated'}
            )
            return self._parse_story(response)
        except Exception as e:
            self.logger.error(f"Failed to get story {key}: {e}")
            return None

    def search_stories(self, query: str) -> List[JiraStory]:
        """Search for stories by text query.

        Args:
            query: Search query string

        Returns:
            List of matching stories
        """
        jql = f'project = "{self.config.project_key}" AND text ~ "{query}"'
        return self.fetch_stories(jql)

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
