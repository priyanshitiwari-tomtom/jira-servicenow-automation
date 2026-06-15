# Jira-ServiceNow Automation Agent

An intelligent automation agent that fetches update sets from Jira stories and creates parent update sets in ServiceNow with all related update sets as children.

## Features

- 🔄 **Automatic Sync**: Periodically fetches Jira stories and syncs to ServiceNow
- 📊 **Parent-Child Hierarchy**: Creates parent update sets with child relationships
- 🛡️ **Error Handling**: Robust error handling and retry logic
- 📝 **Logging**: Comprehensive logging for audit trail
- 🔒 **Secure Configuration**: Environment-based credential management
- 🧪 **Testable**: Unit tests and integration tests included
- 📱 **State Tracking**: Maintains state to prevent duplicate syncs

## Architecture

```
jira-servicenow-agent/
├── src/
│   ├── agent.py                 # Main agent orchestrator
│   ├── jira_client.py          # Jira API integration
│   ├── servicenow_client.py    # ServiceNow API integration
│   ├── models.py               # Data models
│   ├── config.py               # Configuration management
│   ├── logger.py               # Logging setup
│   ├── state_manager.py        # State persistence
│   └── utils.py                # Utility functions
├── tests/
│   ├── test_agent.py
│   ├── test_jira_client.py
│   ├── test_servicenow_client.py
│   └── fixtures.py
├── state/                       # State files (created at runtime)
├── logs/                        # Log files (created at runtime)
├── main.py                      # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.8+
- Jira Cloud instance with API access
- ServiceNow instance with API access
- Git

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/priyanshitiwari003-git/jira-servicenow-automation.git
cd jira-servicenow-automation
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

#### Jira Configuration

1. **JIRA_BASE_URL**: Your Jira instance URL (e.g., https://mycompany.atlassian.net)
2. **JIRA_USERNAME**: Your Jira email
3. **JIRA_API_TOKEN**: [Generate here](https://id.atlassian.com/manage-profile/security/api-tokens)
4. **JIRA_PROJECT_KEY**: The project key containing your stories (e.g., PROJ)
5. **JIRA_UPDATE_SET_FIELD**: Custom field ID storing update set names

#### ServiceNow Configuration

1. **SN_INSTANCE_URL**: Your ServiceNow instance URL
2. **SN_USERNAME**: Your ServiceNow username
3. **SN_PASSWORD**: Your ServiceNow password
4. **SN_TABLE**: Table name (default: sn_chg_management_update_set)

#### Agent Configuration

- **RUN_INTERVAL_MINUTES**: How often to run the sync (default: 60)
- **DRY_RUN**: Set to `True` to preview changes without applying them

### 5. Create Directories

```bash
mkdir -p state logs
```

## Usage

### Run Agent Once

```bash
python main.py --once
```

### Run Agent with Scheduling

```bash
python main.py --schedule
```

### Run with Dry Run (Preview)

```bash
python main.py --once --dry-run
```

### Run Tests

```bash
pytest tests/ -v
pytest tests/ --cov=src  # With coverage
```

## How It Works

### Workflow

1. **Fetch Jira Stories**
   - Queries Jira for stories in the configured project
   - Extracts update set information from custom fields
   - Filters out already processed stories using state tracking

2. **Parse Update Sets**
   - Groups update sets by parent story
   - Validates update set names and references
   - Prepares parent-child relationships

3. **Create in ServiceNow**
   - Creates parent update sets in ServiceNow
   - Associates child update sets to parents
   - Maintains bidirectional references
   - Updates state file to prevent re-processing

4. **Handle Conflicts**
   - Detects existing update sets
   - Updates or skips based on configuration
   - Logs all changes and conflicts

5. **Report Results**
   - Logs successful syncs
   - Reports failures and errors
   - Maintains audit trail

## API Integration Details

### Jira API

- **Endpoint**: `GET /rest/api/3/search`
- **Query**: Searches for stories with update set custom fields
- **Authentication**: Basic auth with API token

### ServiceNow API

- **Endpoint**: `POST /api/now/table/{table_name}`
- **Endpoint**: `PATCH /api/now/table/{table_name}/{sys_id}`
- **Authentication**: Basic auth

## Logging

Logs are written to both console and file (`logs/agent.log`):

```
2024-01-15 10:30:45 | INFO | Agent started | Jira-ServiceNow Agent
2024-01-15 10:30:46 | INFO | Fetched 5 stories from Jira | count=5
2024-01-15 10:30:48 | INFO | Created parent update set | parent_id=CHG0123456
2024-01-15 10:30:49 | INFO | Sync completed successfully | synced=5, failed=0
```

## State Management

The agent maintains state in `state/agent_state.json` to track:

- Last sync timestamp
- Processed Jira story IDs
- Created ServiceNow update set mappings
- Error history

## Error Handling

The agent implements:

- **Retry Logic**: Automatic retries for transient failures
- **Connection Pooling**: Efficient API connection management
- **Rate Limiting**: Respects API rate limits
- **Graceful Degradation**: Continues processing on partial failures
- **Detailed Logging**: Logs all errors with context

## Configuration Examples

### Fetch Only Recent Stories

Modify `jira_client.py` to add JQL filter:

```python
jql = f'project = "{self.project_key}" AND created >= -7d'
```

### Custom ServiceNow Fields

Map additional fields in `servicenow_client.py`:

```python
update_set = {
    'name': story.title,
    'description': story.description,
    'custom_field': story.custom_value
}
```

## Troubleshooting

### Connection Errors

```
ERROR | Failed to connect to Jira
```

**Solution**: Verify `JIRA_BASE_URL` and API token validity

### Authentication Errors

```
ERROR | Authentication failed
```

**Solution**: Verify credentials in `.env` file

### Rate Limiting

```
WARN | Rate limit approaching
```

**Solution**: Increase `RUN_INTERVAL_MINUTES` in configuration

### State File Issues

```bash
# Reset state to start fresh
rm state/agent_state.json
```

## Development

### Add New Integration

1. Create client class in `src/new_client.py`
2. Implement `connect()`, `fetch()`, `create()` methods
3. Add tests in `tests/test_new_client.py`
4. Update agent orchestrator

### Extend Models

Add new fields to `src/models.py`:

```python
class UpdateSet(BaseModel):
    new_field: str
```

## Performance Tuning

- Increase `RUN_INTERVAL_MINUTES` to reduce API calls
- Filter Jira query by date to process fewer stories
- Batch ServiceNow operations for bulk updates
- Monitor logs for performance bottlenecks

## Security Considerations

1. **Never commit `.env` file** - add to `.gitignore`
2. **Rotate API tokens** regularly
3. **Use service accounts** for agent authentication
4. **Encrypt sensitive data** in state files
5. **Audit logs** regularly
6. **Restrict network access** to authorized IPs

## Contributing

To contribute:

1. Create a feature branch
2. Write tests for new features
3. Ensure all tests pass
4. Submit a pull request

## License

MIT License - See LICENSE file

## Support

For issues, questions, or suggestions, please create a GitHub issue in this repository.

## Roadmap

- [ ] Web dashboard for monitoring
- [ ] Webhook-based real-time sync
- [ ] Support for multiple Jira projects
- [ ] Custom transformation rules
- [ ] Slack notifications
- [ ] Database backend for state
- [ ] Docker containerization
