# Airtable/Notion Sync Setup Guide

This document explains how to configure and use the Airtable/Notion sync feature for lightweight collaboration in the YMCA Volunteer PathFinder system.

## Overview

The sync feature enables bidirectional synchronization of volunteer and project data between Airtable and Notion, allowing teams to collaborate using their preferred platform while keeping data consistent across both systems.

## Features

- **Bidirectional Sync**: Sync data from Airtable to Notion, Notion to Airtable, or both directions
- **Conflict Resolution**: Automatic and manual conflict resolution strategies
- **Background Sync**: Automated sync on configurable intervals
- **Error Handling**: Robust retry logic with exponential backoff
- **Field Mapping**: Flexible field mappings between platforms
- **Sync Status**: Real-time sync status and history tracking

## Prerequisites

1. **Airtable Account**: Create an Airtable base with volunteer and project tables
2. **Notion Workspace**: Set up Notion databases for volunteers and projects
3. **API Access**: Obtain API keys for both platforms

### Airtable Setup

1. Create a new base or use an existing one
2. Create tables for:
   - **Volunteers**: Name, Email, Phone, Skills, Interests, Branch Preference, etc.
   - **Projects**: Title, Description, Category, Branch, Skills Needed, etc.
3. Get your Airtable API key from [https://airtable.com/api](https://airtable.com/api)
4. Note your base ID (found in the API documentation for your base)

### Notion Setup

1. Create a new workspace or use an existing one
2. Create databases for:
   - **Volunteers**: Similar structure to Airtable table
   - **Projects**: Similar structure to Airtable table
3. Create a Notion integration at [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
4. Share your databases with the integration
5. Note the database IDs from the URLs

## Configuration

### Environment Variables

Add the following environment variables to your `.env` file:

```env
# Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_VOLUNTEER_TABLE=Volunteers
AIRTABLE_PROJECT_TABLE=Projects

# Notion Configuration
NOTION_API_KEY=your_notion_integration_token
NOTION_VOLUNTEER_DB_ID=your_volunteer_database_id
NOTION_PROJECT_DB_ID=your_project_database_id

# Sync Configuration
SYNC_ENABLED=true
SYNC_INTERVAL_MINUTES=30
SYNC_DIRECTION=bidirectional
CONFLICT_RESOLUTION=notion_wins
```

### Sync Direction Options

- `airtable_to_notion`: Only sync from Airtable to Notion
- `notion_to_airtable`: Only sync from Notion to Airtable  
- `bidirectional`: Sync in both directions (recommended)

### Conflict Resolution Options

- `notion_wins`: Notion data takes precedence in conflicts
- `airtable_wins`: Airtable data takes precedence in conflicts
- `manual`: Conflicts require manual resolution

## Field Mappings

The sync service automatically maps fields between platforms:

### Volunteer Fields
- **Name** → Title (Notion) / Single line text (Airtable)
- **Email** → Email (both platforms)
- **Phone** → Phone number (both platforms)
- **Skills** → Multi-select (both platforms)
- **Interests** → Multi-select (both platforms)
- **Branch Preference** → Single select (both platforms)
- **Experience Level** → Single select (both platforms)
- **Member Status** → Checkbox (both platforms)

### Project Fields
- **Title** → Title (Notion) / Single line text (Airtable)
- **Description** → Rich text (Notion) / Long text (Airtable)
- **Category** → Single select (both platforms)
- **Branch** → Single select (both platforms)
- **Skills Needed** → Multi-select (both platforms)
- **Time Commitment** → Single select (both platforms)
- **Status** → Single select (both platforms)
- **Volunteers Needed** → Number (both platforms)

## API Endpoints

### Sync Management

#### Get Sync Status
```http
GET /api/sync/status
```
Returns current sync status, queue information, and statistics.

#### Start Sync
```http
POST /api/sync/start
Content-Type: application/json

{
  "table_types": ["volunteers", "projects"],
  "scheduled_time": "2025-09-06T20:30:00"
}
```

#### Force Immediate Sync
```http
POST /api/sync/force
Content-Type: application/json

{
  "table_types": ["volunteers"]
}
```

#### Get Task Details
```http
GET /api/sync/task/{task_id}
```

#### Cancel Task
```http
DELETE /api/sync/task/{task_id}
```

### Conflict Management

#### Get Conflicts
```http
GET /api/sync/conflicts
```

#### Resolve Conflict
```http
POST /api/sync/conflicts/resolve
Content-Type: application/json

{
  "conflict_id": "conflict_123",
  "resolution": "accept_source",
  "resolved_data": {}
}
```

### System Control

#### Enable Background Sync
```http
POST /api/sync/enable
```

#### Disable Background Sync
```http
POST /api/sync/disable
```

#### Get Field Mappings
```http
GET /api/sync/mappings
```

## Usage Examples

### Python Client Example

```python
import httpx

async def sync_volunteers():
    async with httpx.AsyncClient() as client:
        # Start a sync for volunteers only
        response = await client.post(
            "http://localhost:8000/api/sync/start",
            json={"table_types": ["volunteers"]}
        )
        task_id = response.json()["task_id"]
        
        # Check task status
        status = await client.get(f"http://localhost:8000/api/sync/task/{task_id}")
        print(status.json())
```

### cURL Examples

```bash
# Check sync status
curl -X GET http://localhost:8000/api/sync/status

# Force sync of all tables
curl -X POST http://localhost:8000/api/sync/force \
  -H "Content-Type: application/json" \
  -d '{"table_types": ["volunteers", "projects"]}'

# Get conflicts
curl -X GET http://localhost:8000/api/sync/conflicts

# Resolve a conflict
curl -X POST http://localhost:8000/api/sync/conflicts/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "conflict_id": "conflict_123",
    "resolution": "accept_source"
  }'
```

## Monitoring

### Sync Status Response

```json
{
  "is_syncing": false,
  "last_sync": {
    "start_time": "2025-09-06T20:19:30.301Z",
    "end_time": "2025-09-06T20:21:15.498Z",
    "tables_synced": [
      {
        "table_type": "volunteers",
        "records_processed": 150,
        "created": 5,
        "updated": 12,
        "conflicts_detected": 2,
        "errors": []
      }
    ],
    "records_processed": 150,
    "conflicts_detected": 2,
    "duration_seconds": 105.2
  },
  "conflicts_pending": 2,
  "manager_status": {
    "is_running": true,
    "sync_enabled": true,
    "queue_size": 0,
    "history_size": 10
  }
}
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Check API keys are correct and active
   - Ensure Notion integration has access to databases
   - Verify Airtable base permissions

2. **Sync Failures**
   - Check network connectivity
   - Verify database/table structures match expected fields
   - Review error logs for specific issues

3. **Conflicts**
   - Review conflict queue via `/api/sync/conflicts`
   - Choose appropriate conflict resolution strategy
   - Consider adjusting sync intervals to reduce conflicts

### Logs

The sync service logs detailed information about:
- Sync operations and results
- Error conditions and retries
- Conflict detection and resolution
- Rate limiting and delays

Check the application logs for detailed troubleshooting information.

## Best Practices

1. **Field Structure**: Keep field names and types consistent between platforms
2. **Sync Intervals**: Use appropriate intervals (15-60 minutes) to balance freshness with API limits
3. **Conflict Resolution**: Choose resolution strategy based on your team's workflow
4. **Monitoring**: Regularly check sync status and resolve conflicts promptly
5. **Data Validation**: Validate data quality before syncing to avoid propagating errors
6. **Backup**: Keep backups of important data before major sync operations

## Security Considerations

- Store API keys securely as environment variables
- Use HTTPS for all API communications
- Implement proper access controls for sync endpoints
- Monitor sync logs for suspicious activity
- Regularly rotate API keys

## Support

For issues with the sync feature:
1. Check the sync status endpoint
2. Review application logs
3. Verify configuration settings
4. Test connectivity to both platforms
5. Contact your system administrator

## Future Enhancements

Planned improvements include:
- Custom field mapping configuration
- Webhook-based real-time sync
- Advanced conflict resolution rules
- Sync analytics dashboard
- Multi-workspace support