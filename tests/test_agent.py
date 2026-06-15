"""Tests for the main agent."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agent import JiraServiceNowAgent
from src.config import AppConfig, JiraConfig, ServiceNowConfig, AgentConfig
from src.models import JiraStory, SyncResult
from datetime import datetime


@pytest.fixture
def app_config():
    """Create test app config."""
    return AppConfig(
        jira=JiraConfig(
            base_url='https://test.atlassian.net',
            username='test@example.com',
            api_token='test-token',
            project_key='TEST',
            update_set_field='customfield_10001'
        ),
        servicenow=ServiceNowConfig(
            instance_url='https://test.service-now.com',
            username='testuser',
            password='testpass',
            table='sn_chg_management_update_set'
        ),
        agent=AgentConfig(
            name='Test Agent',
            log_level='DEBUG',
            run_interval_minutes=60,
            dry_run=False,
            state_file_path='/tmp/test_state.json',
            log_file_path='/tmp/test.log'
        )
    )


@patch('src.agent.JiraClient')
@patch('src.agent.ServiceNowClient')
@patch('src.agent.StateManager')
def test_agent_init(mock_state_manager, mock_sn_client, mock_jira_client, app_config):
    """Test agent initialization."""
    agent = JiraServiceNowAgent(app_config)

    assert agent.config == app_config


@patch('src.agent.JiraClient')
@patch('src.agent.ServiceNowClient')
@patch('src.agent.StateManager')
def test_run_once_no_stories(mock_state_manager, mock_sn_client, mock_jira_client, app_config):
    """Test running once with no stories."""
    mock_jira_instance = MagicMock()
    mock_jira_instance.fetch_stories.return_value = []
    mock_jira_client.return_value = mock_jira_instance

    agent = JiraServiceNowAgent(app_config)
    result = agent.run_once()

    assert result.success
    assert result.total_stories == 0
