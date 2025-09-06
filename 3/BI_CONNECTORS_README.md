# External BI Connectors

This module provides comprehensive support for exporting and refreshing data in external Business Intelligence (BI) systems including Power BI, Looker, and Google Sheets.

## Features

- **Multi-Platform Support**: Power BI, Looker, and Google Sheets
- **Automated Data Export**: Push volunteer data to BI systems
- **Scheduled Refresh**: Automatic dataset refresh with cron-like scheduling
- **Real-time Status Tracking**: Monitor export jobs and refresh operations
- **RESTful API**: Complete REST API for connector management
- **Background Processing**: Non-blocking operations with job status tracking

## Architecture

### Core Components

1. **BIConnectorInterface**: Abstract base class for all connectors
2. **PowerBIConnector**: Microsoft Power BI integration
3. **LookerConnector**: Looker platform integration
4. **GoogleSheetsConnector**: Google Sheets integration
5. **BIConnectorManager**: Central manager for all connectors
6. **Scheduler**: Background scheduler for automated refresh operations

### Data Flow

```
Volunteer Data → BIConnectorManager → Specific Connector → External BI System
                      ↓
              Export Job Tracking
                      ↓
              Scheduled Refresh
```

## Installation

### Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

Key dependencies for BI connectors:
- `google-api-python-client>=2.110.0` - Google Sheets API
- `google-auth>=2.25.2` - Google authentication
- `msal>=1.25.0` - Microsoft authentication
- `croniter>=2.0.1` - Cron expression parsing
- `pyarrow>=14.0.1` - Data serialization
- `pandas>=2.3.2` - Data manipulation
- `requests>=2.31.0` - HTTP requests

## Configuration

### Power BI Setup

1. **Azure App Registration**:
   - Go to Azure Portal → App Registrations
   - Create new registration
   - Get Client ID and Client Secret
   - Grant Power BI service permissions

2. **Power BI Workspace**:
   - Create or identify target workspace
   - Create dataset with appropriate schema
   - Note Workspace ID and Dataset ID

3. **Configuration**:
   ```python
   power_bi_config = ConnectorConfig(
       name="ymca_powerbi",
       connector_type=ConnectorType.POWER_BI,
       client_id="your-client-id",
       client_secret="your-client-secret",
       workspace_id="your-workspace-id",
       dataset_id="your-dataset-id"
   )
   ```

### Looker Setup

1. **API Credentials**:
   - Go to Looker Admin → Users → API3 Credentials
   - Generate Client ID and Client Secret

2. **Model Configuration**:
   - Identify target model and view names
   - Ensure API user has appropriate permissions

3. **Configuration**:
   ```python
   looker_config = ConnectorConfig(
       name="ymca_looker",
       connector_type=ConnectorType.LOOKER,
       client_id="your-client-id",
       client_secret="your-client-secret",
       base_url="https://your-instance.looker.com:19999/api/4.0",
       workspace_id="your-model-name",
       dataset_id="your-view-name"
   )
   ```

### Google Sheets Setup

1. **Service Account**:
   - Go to Google Cloud Console
   - Create service account
   - Download JSON key file
   - Enable Google Sheets API

2. **Sheet Permissions**:
   - Share target Google Sheet with service account email
   - Grant Editor permissions

3. **Configuration**:
   ```python
   google_sheets_config = ConnectorConfig(
       name="ymca_sheets",
       connector_type=ConnectorType.GOOGLE_SHEETS,
       dataset_id="your-google-sheet-id",
       service_account_key={
           "type": "service_account",
           "project_id": "your-project-id",
           # ... full service account key JSON
       }
   )
   ```

## Usage

### Basic Setup

```python
from bi_connectors import (
    BIConnectorManager, 
    ConnectorConfig, 
    ConnectorType,
    bi_connector_manager
)

# Register connectors
success = bi_connector_manager.register_connector(power_bi_config)
success = bi_connector_manager.register_connector(looker_config)
success = bi_connector_manager.register_connector(google_sheets_config)

# Test connections
results = await bi_connector_manager.test_all_connectors()
```

### Data Export

```python
import pandas as pd

# Prepare volunteer data
volunteer_data = pd.DataFrame({
    'volunteer_id': [1, 2, 3],
    'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
    'hours': [10.5, 25.0, 8.5],
    'branch': ['Downtown', 'North', 'South']
})

# Export to Power BI
job = await bi_connector_manager.export_data_to_connector(
    connector_name="ymca_powerbi",
    data=volunteer_data,
    table_name="volunteer_data",
    format=ExportFormat.JSON
)

# Check job status
print(f"Job ID: {job.id}, Status: {job.status}")
```

### Scheduled Refresh

```python
from bi_connectors import RefreshSchedule

# Create refresh schedule
schedule = RefreshSchedule(
    connector_name="ymca_powerbi",
    cron_expression="0 */6 * * *",  # Every 6 hours
    enabled=True
)

bi_connector_manager.add_refresh_schedule(schedule)
```

## API Endpoints

### Connector Management

- `POST /api/bi-connectors/register` - Register new connector
- `GET /api/bi-connectors` - List all connectors
- `POST /api/bi-connectors/{name}/test` - Test connection
- `DELETE /api/bi-connectors/{name}` - Remove connector

### Data Export

- `POST /api/bi-connectors/export` - Export data to BI system
- `GET /api/bi-connectors/export-jobs/{job_id}` - Get export job status

### Refresh Operations

- `POST /api/bi-connectors/{name}/refresh` - Manual refresh
- `POST /api/bi-connectors/schedules` - Create refresh schedule
- `GET /api/bi-connectors/schedules` - List all schedules

### Example API Requests

#### Register Power BI Connector
```bash
curl -X POST "http://localhost:8000/api/bi-connectors/register" \
-H "Content-Type: application/json" \
-d '{
  "name": "ymca_powerbi",
  "connector_type": "power_bi",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "workspace_id": "your-workspace-id",
  "dataset_id": "your-dataset-id"
}'
```

#### Export Data
```bash
curl -X POST "http://localhost:8000/api/bi-connectors/export" \
-H "Content-Type: application/json" \
-d '{
  "connector_name": "ymca_powerbi",
  "table_name": "volunteer_data",
  "export_format": "json"
}'
```

#### Create Refresh Schedule
```bash
curl -X POST "http://localhost:8000/api/bi-connectors/schedules" \
-H "Content-Type: application/json" \
-d '{
  "connector_name": "ymca_powerbi",
  "cron_expression": "0 */6 * * *",
  "enabled": true
}'
```

## Cron Expression Examples

| Schedule | Cron Expression | Description |
|----------|-----------------|-------------|
| Every hour | `0 * * * *` | Run at minute 0 of every hour |
| Every 6 hours | `0 */6 * * *` | Run every 6 hours |
| Daily at 2 AM | `0 2 * * *` | Run daily at 2:00 AM |
| Weekdays at 9 AM | `0 9 * * 1-5` | Run weekdays at 9:00 AM |
| Every Sunday at midnight | `0 0 * * 0` | Run every Sunday at 00:00 |

## Error Handling

### Common Error Scenarios

1. **Authentication Failures**:
   - Invalid credentials
   - Expired tokens
   - Insufficient permissions

2. **Data Export Errors**:
   - Network connectivity issues
   - Schema mismatches
   - Rate limiting

3. **Refresh Failures**:
   - Dataset not found
   - Service unavailable
   - Invalid schedule expressions

### Error Response Format

```json
{
  "success": false,
  "error": "Authentication failed: Invalid client credentials",
  "connector_name": "ymca_powerbi",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Monitoring and Logging

### Job Status Tracking

Export jobs provide detailed status information:

```python
job = bi_connector_manager.get_export_job(job_id)
print(f"Status: {job.status}")
print(f"Records: {job.record_count}")
print(f"Started: {job.started_at}")
print(f"Completed: {job.completed_at}")
if job.error_message:
    print(f"Error: {job.error_message}")
```

### Logging

The system uses Python's logging module with the following levels:

- `INFO`: Successful operations, job completions
- `WARNING`: Recoverable issues, fallback usage
- `ERROR`: Failed operations, authentication errors
- `DEBUG`: Detailed operation logs (when debug enabled)

Configure logging in your application:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bi_connectors')
```

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
python -m pytest test_bi_connectors.py -v
```

Test categories:
- Connector registration and management
- Authentication mechanisms
- Data export operations
- Schedule management
- Error handling scenarios

### Integration Testing

Use the provided usage examples:

```bash
python bi_connectors_usage.py
```

This demonstrates:
- Connector configuration
- Data export workflows
- Schedule setup
- Error scenarios

## Security Considerations

### Credential Management

- Store credentials securely (environment variables, key management systems)
- Use service accounts with minimal required permissions
- Rotate credentials regularly
- Never commit credentials to version control

### API Security

- Use HTTPS in production
- Implement API authentication/authorization
- Rate limiting for API endpoints
- Audit logging for sensitive operations

### Data Privacy

- Ensure compliance with data protection regulations
- Implement data encryption in transit and at rest
- Regular security audits of BI system access
- Monitor for unauthorized access attempts

## Performance Considerations

### Data Volume

- Large datasets may require chunking
- Consider incremental updates vs full refresh
- Monitor API rate limits
- Implement retry logic with exponential backoff

### Concurrent Operations

- Limit concurrent export jobs
- Queue management for high-volume scenarios
- Resource monitoring and alerting
- Graceful degradation under load

## Troubleshooting

### Common Issues

1. **Connection Timeouts**:
   ```python
   # Increase timeout in requests
   response = requests.post(url, json=data, timeout=300)
   ```

2. **Memory Issues with Large Datasets**:
   ```python
   # Process data in chunks
   for chunk in pd.read_csv('data.csv', chunksize=1000):
       await export_data(chunk)
   ```

3. **Rate Limiting**:
   ```python
   # Implement exponential backoff
   import time
   import random
   
   def retry_with_backoff(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except RateLimitError:
               wait_time = (2 ** attempt) + random.uniform(0, 1)
               time.sleep(wait_time)
   ```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger('bi_connectors').setLevel(logging.DEBUG)
```

## Contributing

### Development Setup

1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest test_bi_connectors.py`
4. Check code style: `black bi_connectors.py`

### Adding New Connectors

1. Create new connector class inheriting from `BIConnectorInterface`
2. Implement required methods: `authenticate`, `export_data`, `refresh_dataset`, etc.
3. Add connector type to `ConnectorType` enum
4. Update `BIConnectorManager.register_connector` method
5. Add comprehensive tests
6. Update documentation

## License

This BI Connectors module is part of the YMCA Volunteer PathFinder system and follows the same licensing terms as the main project.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review test cases for usage examples
3. Create an issue with detailed error information
4. Include relevant log outputs and configuration details