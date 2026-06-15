# Jira-ServiceNow Deployment Automation Agent

An intelligent automation agent that fetches Jira stories in "Ready for Deployment" status, extracts ServiceNow update set links from story comments, and creates a parent deployment update set in ServiceNow with all update sets as children. Sends detailed deployment reports to Microsoft Teams.

## Features

- 🔍 **Smart Story Fetching**: Automatically finds stories in "Ready for Deployment" status
- 📝 **Comment Parsing**: Extracts ServiceNow update set links and IDs from story comments
- 📦 **Hierarchy Creation**: Creates parent deployment update set with child update sets
- 🎯 **Sprint Aware**: Links deployment to current Jira sprint
- 💬 **Teams Reports**: Sends detailed deployment reports to Microsoft Teams channel
- ⏱️ **Scheduled Runs**: Automatically runs every Thursday morning (configurable)
- 📊 **State Tracking**: Maintains state to track processed stories and created update sets
- 🛡️ **Error Handling**: Robust error handling with Teams notifications
- 🔐 **Secure Config**: Environment-based credential management

## Prerequisites

- Python 3.8+
- Jira Cloud instance with API access
- ServiceNow instance with API access
- Microsoft Teams incoming webhook
- Git

## Architecture

```
jira-servicenow-automation/
├── src/
│   ├── agent.py                    # Main deployment agent
│   ├── jira_client.py             # Jira API + comment parsing
│   ├── servicenow_client.py       # ServiceNow API integration
│   ├── teams_notifier.py          # Microsoft Teams integration
│   ├── config.py                  # Configuration management
│   ├── models.py                  # Data models
│   ├── logger.py                  # Structured logging
│   ├── state_manager.py           # State persistence
│   └── utils.py                   # Utility functions
├── tests/                          # Test suite
├── main.py                         # Entry point with scheduling
├── requirements.txt                # Dependencies
├── .env.example                    # Configuration template
└── README.md                       # This file
```

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
# Edit .env with your credentials
```

### Configuration Details

#### Jira Configuration

- **JIRA_BASE_URL**: Your Jira instance URL (e.g., https://mycompany.atlassian.net)
- **JIRA_USERNAME**: Your Jira email
- **JIRA_API_TOKEN**: [Generate API token](https://id.atlassian.com/manage-profile/security/api-tokens)
- **JIRA_PROJECT_KEY**: Your project key (e.g., PROJ, DEV)
- **JIRA_BOARD_ID**: Jira board ID (used to fetch current sprint)
- **JIRA_STORY_STATUS**: Status name (default: "Ready for Deployment")

#### ServiceNow Configuration

- **SN_INSTANCE_URL**: Your ServiceNow instance URL
- **SN_USERNAME**: ServiceNow username
- **SN_PASSWORD**: ServiceNow password
- **SN_TABLE**: Table name (default: sn_chg_management_update_set)

#### Teams Configuration

- **TEAMS_WEBHOOK_URL**: Microsoft Teams incoming webhook URL
  - [Create webhook](https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/connectors-using)
  - Format: `https://outlook.webhook.office.com/webhookb2/...`

#### Agent Configuration

- **RUN_ON_THURSDAY**: Set to `True` to run on Thursdays (default: True)
- **RUN_TIME**: Run time in HH:MM format (default: 09:00)
- **DRY_RUN**: Set to `True` to preview without making changes

### 5. Create Directories

```bash
mkdir -p state logs
```

## Usage

### Run Immediately

```bash
python main.py --run
```

### Preview Changes (Dry Run)

```bash
python main.py --run --dry-run
```

### Schedule for Thursdays at 9:00 AM

```bash
python main.py --schedule
```

### Reset Agent State

```bash
python main.py --reset-state
```

### Run Tests

```bash
pytest tests/ -v
pytest tests/ --cov=src  # With coverage
```

## How It Works

### 1. Fetch Stories

```
Agent queries Jira for stories with status = "Ready for Deployment"
Filters by project and status
Fetches all story metadata and comments
```

### 2. Extract Update Set Links

```
Parses story comments for patterns:
  - Full URLs: https://instance.service-now.com/...?sys_id=xxxxx
  - Update set names: us_xxxxx, update_set_xxxxx
  - Manual references: "UpdateSet: xxxxx"
Extracts unique update set identifiers
```

### 3. Get Current Sprint

```
Fetches active sprint from Jira board
Uses sprint name in naming convention
```

### 4. Create Parent Update Set

```
Generates name: DEPLOYMENT-{SPRINT}-{DATE}
Example: DEPLOYMENT-SPRINT-12-2024-06-15
Creates parent in ServiceNow
```

### 5. Create Child Update Sets

```
For each update set extracted:
  - Creates child record in ServiceNow
  - Links to parent update set
  - References Jira story for traceability
```

### 6. Send Teams Report

```
Builds card with:
  - Deployment summary (stories, counts)
  - Per-story breakdown (assignee, update sets)
  - Link to parent in ServiceNow
Posts to Teams webhook
```

## Teams Report Format

The agent sends formatted card messages to Teams:

```
📦 Deployment Report - SPRINT-12

Status: ✅ Success
Sprint: SPRINT-12
Total Stories: 5
Synced: 5
Failed: 0
Skipped: 0
Parent Update Set: DEPLOYMENT-SPRINT-12-2024-06-15

📝 PROJ-123
  Story: Add user authentication
  Assigned To: John Doe
  Update Sets: 3
    • us_auth_001
    • us_auth_002
    • us_auth_003

[View in ServiceNow]
```

## Comment Parsing Examples

### Supported Formats

**Full ServiceNow URL:**
```
Deployed to: https://mycompany.service-now.com/nav_to.do?uri=table/sn_chg_management_update_set.do?sys_id=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**Update Set Name:**
```
UpdateSet: us_authentication_module
```

**Multiple References:**
```
Changes:
- UpdateSet: us_api_gateway
- us_database_migration
- sys_id=12345678901234567890123456789012
```

## Logging

Logs are written to:

- **Console**: Colored output for real-time monitoring
- **File**: JSON formatted logs in `logs/agent.log`

### Log Examples

```json
{"timestamp": "2024-06-15T09:00:00", "level": "INFO", "message": "Fetched 5 stories in 'Ready for Deployment' status"}
{"timestamp": "2024-06-15T09:01:00", "level": "INFO", "message": "Created parent update set", "name": "DEPLOYMENT-SPRINT-12-2024-06-15", "sys_id": "abc123"}
```

## State Management

Agent state is persisted in `state/agent_state.json`:

```json
{
  "last_sync_time": "2024-06-15T09:05:00",
  "last_parent_created": "sys_id_123",
  "processed_stories": ["PROJ-123", "PROJ-124"],
  "successful_syncs": 42,
  "failed_syncs": 1
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

**Solution**: Check credentials in `.env` file

### No Update Sets Found

```
WARN | Story has no update set links
```

**Solution**: Ensure comments contain update set links in supported formats

### Teams Webhook Errors

```
ERROR | Failed to send Teams message
```

**Solution**: Verify webhook URL and Teams connectivity

### Reset State

```bash
rm state/agent_state.json
python main.py --reset-state
```

## Development

### Add Custom Update Set Pattern

Edit `src/jira_client.py` `_parse_update_sets_from_text()` method:

```python
# Pattern 5: Your custom format
pattern5 = r'your-custom-regex-here'
matches = re.findall(pattern5, text)
update_sets.extend(matches)
```

### Customize Teams Report

Edit `src/teams_notifier.py` `_build_message()` method to change card layout, colors, or fields.

### Add Story Filter

Edit `src/jira_client.py` `fetch_ready_for_deployment_stories()` to add JQL filters:

```python
jql = f'project = "{self.config.project_key}" AND status = "{self.config.story_status}" AND assignee is not EMPTY'
```

## Performance Tuning

- **Large Story Counts**: Increase `maxResults` in paginated requests
- **Comment Parsing**: Cache comment parsing results
- **ServiceNow Bulk**: Batch child update set creation
- **Rate Limiting**: Add backoff logic for API calls

## Security Considerations

1. **Never commit `.env` file** - it contains secrets
2. **Rotate API tokens** regularly
3. **Use service accounts** for agent authentication
4. **Encrypt sensitive data** if storing locally
5. **Audit logs** for compliance
6. **Restrict network access** to authorized IPs

## Contributing

1. Create feature branch
2. Write tests for new features
3. Ensure all tests pass
4. Submit pull request

## License

MIT License - See LICENSE file

## Support

For issues, questions, or suggestions, create a GitHub issue.

## Roadmap

- [ ] Web dashboard for monitoring
- [ ] Slack integration
- [ ] Email notifications
- [ ] Multi-project support
- [ ] Custom field mapping
- [ ] Webhook-based real-time sync
- [ ] Docker containerization
- [ ] Database backend for state
