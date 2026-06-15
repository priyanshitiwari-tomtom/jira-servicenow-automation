"""Tests for ServiceNow client."""

import pytest
from unittest.mock import MagicMock, patch
from src.servicenow_client import ServiceNowClient
from src.config import ServiceNowConfig
from src.models import UpdateSet


@pytest.fixture
def sn_config():
    """Create test ServiceNow config."""
    return ServiceNowConfig(
        instance_url='https://test.service-now.com',
        username='testuser',
        password='testpass',
        table='sn_chg_management_update_set'
    )


@pytest.fixture
def sn_client(sn_config):
    """Create test ServiceNow client."""
    return ServiceNowClient(sn_config)


def test_servicenow_client_init(sn_client):
    """Test ServiceNow client initialization."""
    assert sn_client.instance_url == 'https://test.service-now.com'
    assert sn_client.table == 'sn_chg_management_update_set'


@patch('requests.Session.request')
def test_create_update_set(mock_request, sn_client):
    """Test creating update set."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'result': {
            'sys_id': '12345',
            'name': 'test_update_set'
        }
    }
    mock_request.return_value = mock_response

    update_set = UpdateSet(
        name='test_update_set',
        description='Test',
        type='regular'
    )

    sys_id = sn_client.create_update_set(update_set)

    assert sys_id == '12345'


def test_create_update_set_dry_run(sn_client):
    """Test creating update set in dry run mode."""
    update_set = UpdateSet(
        name='test_update_set',
        description='Test',
        type='regular'
    )

    sys_id = sn_client.create_update_set(update_set, dry_run=True)

    assert sys_id.startswith('dry_run_')


@patch('requests.Session.request')
def test_create_parent_with_children(mock_request, sn_client):
    """Test creating parent with children."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'result': {
            'sys_id': '99999',
            'name': 'parent_test'
        }
    }
    mock_request.return_value = mock_response

    parent_sys_id = sn_client.create_parent_with_children(
        parent_name='parent_test',
        child_names=['child1', 'child2'],
        jira_story_key='TEST-1'
    )

    assert parent_sys_id is not None
