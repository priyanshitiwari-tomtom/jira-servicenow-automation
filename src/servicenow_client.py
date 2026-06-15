"""ServiceNow API client for creating and managing update sets."""

import requests
from typing import List, Optional, Dict, Any
from requests.auth import HTTPBasicAuth
from src.config import ServiceNowConfig
from src.models import UpdateSet
from src.logger import LoggerMixin


class ServiceNowClient(LoggerMixin):
    """Client for interacting with ServiceNow API."""

    def __init__(self, config: ServiceNowConfig):
        """Initialize ServiceNow client.

        Args:
            config: ServiceNow configuration
        """
        self.config = config
        self.instance_url = config.instance_url.rstrip('/')
        self.auth = HTTPBasicAuth(config.username, config.password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({'Content-Type': 'application/json'})
        self.table = config.table

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request to ServiceNow.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Response JSON

        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.instance_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"ServiceNow API error: {e}")
            raise

    def create_update_set(self, update_set: UpdateSet, dry_run: bool = False) -> Optional[str]:
        """Create an update set in ServiceNow.

        Args:
            update_set: UpdateSet object
            dry_run: If True, don't actually create

        Returns:
            Created sys_id or None
        """
        if dry_run:
            self.logger.info(f"[DRY RUN] Would create update set | name={update_set.name}")
            return f"dry_run_{update_set.name}"

        payload = {
            'name': update_set.name,
            'description': update_set.description or '',
            'type': update_set.type,
            'state': 'in_progress',
        }

        if update_set.parent_update_set:
            payload['parent'] = update_set.parent_update_set

        try:
            response = self._make_request(
                'POST',
                f'/api/now/table/{self.table}',
                json=payload
            )

            result = response.get('result', {})
            sys_id = result.get('sys_id')

            self.logger.info(f"Created update set | name={update_set.name} | sys_id={sys_id}")
            return sys_id

        except Exception as e:
            self.logger.error(f"Failed to create update set {update_set.name}: {e}")
            return None

    def update_update_set(self, sys_id: str, updates: Dict[str, Any], dry_run: bool = False) -> bool:
        """Update an existing update set.

        Args:
            sys_id: SystemNow system ID
            updates: Dictionary of fields to update
            dry_run: If True, don't actually update

        Returns:
            True if successful
        """
        if dry_run:
            self.logger.info(f"[DRY RUN] Would update update set | sys_id={sys_id} | updates={updates}")
            return True

        try:
            self._make_request(
                'PATCH',
                f'/api/now/table/{self.table}/{sys_id}',
                json=updates
            )
            self.logger.info(f"Updated update set | sys_id={sys_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update update set {sys_id}: {e}")
            return False

    def get_update_set(self, name: str) -> Optional[Dict[str, Any]]:
        """Get an update set by name.

        Args:
            name: Update set name

        Returns:
            Update set data or None
        """
        try:
            response = self._make_request(
                'GET',
                f'/api/now/table/{self.table}',
                params={'sysparm_query': f'name={name}', 'sysparm_limit': 1}
            )

            results = response.get('result', [])
            if results:
                return results[0]
            return None
        except Exception as e:
            self.logger.error(f"Failed to get update set {name}: {e}")
            return None

    def get_update_set_by_sys_id(self, sys_id: str) -> Optional[Dict[str, Any]]:
        """Get an update set by sys_id.

        Args:
            sys_id: ServiceNow system ID

        Returns:
            Update set data or None
        """
        try:
            response = self._make_request(
                'GET',
                f'/api/now/table/{self.table}/{sys_id}'
            )
            return response.get('result')
        except Exception as e:
            self.logger.error(f"Failed to get update set {sys_id}: {e}")
            return None

    def create_parent_with_children(self, parent_name: str, child_names: List[str],
                                   jira_story_key: Optional[str] = None,
                                   dry_run: bool = False) -> Optional[str]:
        """Create a parent update set with children.

        Args:
            parent_name: Parent update set name
            child_names: List of child update set names
            jira_story_key: Optional Jira story key for reference
            dry_run: If True, don't actually create

        Returns:
            Parent sys_id or None
        """
        self.logger.info(f"Creating parent update set with {len(child_names)} children | parent={parent_name}")

        # Create parent
        parent = UpdateSet(
            name=parent_name,
            description=f"Parent update set for {jira_story_key}" if jira_story_key else "Parent update set",
            type='parent',
            jira_story_key=jira_story_key,
            status='in_progress'
        )

        parent_sys_id = self.create_update_set(parent, dry_run=dry_run)
        if not parent_sys_id:
            return None

        # Create children
        for child_name in child_names:
            child = UpdateSet(
                name=child_name,
                description=f"Child of {parent_name}",
                parent_update_set=parent_sys_id,
                type='child',
                jira_story_key=jira_story_key,
                status='in_progress'
            )
            self.create_update_set(child, dry_run=dry_run)

        self.logger.info(f"Successfully created parent with children | parent_sys_id={parent_sys_id}")
        return parent_sys_id

    def get_all_update_sets(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all update sets matching query.

        Args:
            query: Optional query filter

        Returns:
            List of update sets
        """
        try:
            params = {'sysparm_limit': 500}
            if query:
                params['sysparm_query'] = query

            response = self._make_request(
                'GET',
                f'/api/now/table/{self.table}',
                params=params
            )

            return response.get('result', [])
        except Exception as e:
            self.logger.error(f"Failed to get update sets: {e}")
            return []

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
