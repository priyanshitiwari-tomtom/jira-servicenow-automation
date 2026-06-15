"""Tests for Jira client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.jira_client import JiraClient
from src.config import JiraConfig
from src.models import JiraStory


@pytest.fixture
def jira_config():
    """Create test Jira config."""
    return JiraConfig(
        base_url='https://test.atlassian.net',
        username='test@example.com',
        api_token='test-token',
        project_key='TEST',
        update_set_field='customfield_10001'
    )


@pytest.fixture
def jira_client(jira_config):
    """Create test Jira client."""
    return JiraClient(jira_config)


def test_jira_client_init(jira_client):
    """Test Jira client initialization."""
    assert jira_client.config.project_key == 'TEST'
    assert jira_client.base_url == 'https://test.atlassian.net'


@patch('requests.Session.request')
def test_fetch_stories(mock_request, jira_client):
    """Test fetching stories."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'issues': [
            {
                'key': 'TEST-1',
                'fields': {
                    'summary': 'Test Story',
                    'description': 'Test Description',
                    'status': {'name': 'In Progress'},
                    'customfield_10001': 'UpdateSet1',
                    'created': '2024-01-01T00:00:00.000000Z',
                    'updated': '2024-01-01T00:00:00.000000Z',
                }
            }
        ],
        'total': 1,
        'startAt': 0,
        'maxResults': 50
    }
    mock_request.return_value = mock_response

    stories = jira_client.fetch_stories()

    assert len(stories) == 1
    assert stories[0].key == 'TEST-1'
    assert stories[0].summary == 'Test Story'


def test_extract_update_sets(jira_client):
    """Test extracting update sets from fields."""
    fields = {
        'customfield_10001': 'UpdateSet1',
        'description': 'Test with UpdateSet: ABC123'
    }

    update_sets = jira_client._extract_update_sets(fields)

    assert 'UpdateSet1' in update_sets
    assert 'ABC123' in update_sets


def test_extract_update_sets_list(jira_client):
    """Test extracting multiple update sets."""
    fields = {
        'customfield_10001': ['UpdateSet1', 'UpdateSet2', 'UpdateSet3'],
    }

    update_sets = jira_client._extract_update_sets(fields)

    assert len(update_sets) >= 3
    assert 'UpdateSet1' in update_sets
