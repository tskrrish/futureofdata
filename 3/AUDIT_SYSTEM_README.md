# Audit Log System

This document describes the comprehensive audit logging system implemented for the YMCA Volunteer PathFinder application.

## Overview

The audit log system provides complete change tracking with diff generation and export functionality. It logs who changed what and when, with detailed diffs of all changes.

## Features

- **Complete Change Tracking**: Tracks all CREATE, UPDATE, DELETE operations across all resources
- **Diff Generation**: Automatic generation of human-readable diffs showing exactly what changed
- **Export Functionality**: Export audit logs in CSV, JSON, and Excel formats
- **Filtering and Search**: Advanced filtering by user, resource, action, date range, etc.
- **Statistics and Analytics**: Get insights into system usage and user activity
- **Resource History**: Complete history of changes for any resource
- **User Activity Tracking**: Track all activities for specific users

## Architecture

### Core Components

1. **AuditLogger**: Main audit logging service
2. **AuditEntry**: Data structure for audit log entries
3. **Database Integration**: Automatic audit logging for database operations
4. **API Endpoints**: RESTful endpoints for retrieving and exporting audit data

### Database Schema

The system uses a `audit_logs` table with the following structure:

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE,
    user_id UUID,
    session_id VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    resource VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    changes JSONB,
    diff_text TEXT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
);
```

## API Endpoints

### Get Audit Logs
```
GET /api/audit/logs
```

Query Parameters:
- `user_id`: Filter by user ID
- `resource`: Filter by resource type (user, user_preferences, conversation, etc.)
- `resource_id`: Filter by specific resource ID
- `action`: Filter by action (create, update, delete, view, etc.)
- `start_date`: Filter by start date (ISO format)
- `end_date`: Filter by end date (ISO format)
- `limit`: Number of results to return (default: 100)
- `offset`: Pagination offset (default: 0)

Example:
```bash
curl "http://localhost:8000/api/audit/logs?user_id=123&action=update&limit=50"
```

### Get Resource History
```
GET /api/audit/resource/{resource}/{resource_id}
```

Example:
```bash
curl "http://localhost:8000/api/audit/resource/user/123"
```

### Get User Activity
```
GET /api/audit/user/{user_id}/activity?days=30
```

Example:
```bash
curl "http://localhost:8000/api/audit/user/123/activity?days=7"
```

### Get Audit Statistics
```
GET /api/audit/statistics?days=30
```

Returns comprehensive statistics about system usage.

### Export Audit Logs
```
POST /api/audit/export
```

Request Body:
```json
{
  "format_type": "csv",
  "user_id": "optional-user-id",
  "resource": "optional-resource-type",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z"
}
```

Supported formats: `csv`, `json`, `excel`

## Usage Examples

### Basic Audit Logging

```python
from audit_logger import AuditLogger, AuditAction, AuditResource

# Initialize
audit_logger = AuditLogger(database)

# Log a create action
await audit_logger.log_audit_entry(
    action=AuditAction.CREATE,
    resource=AuditResource.USER,
    user_id="user-123",
    resource_id="user-123",
    new_values={"name": "John Doe", "email": "john@example.com"},
    ip_address="192.168.1.1",
    metadata={"source": "web_registration"}
)

# Log an update with diff
await audit_logger.log_audit_entry(
    action=AuditAction.UPDATE,
    resource=AuditResource.USER,
    user_id="user-123",
    resource_id="user-123",
    old_values={"name": "John Doe", "email": "john@example.com"},
    new_values={"name": "John Smith", "email": "john.smith@example.com"},
    metadata={"updated_fields": ["name", "email"]}
)
```

### Retrieving Audit Data

```python
# Get recent activity for a user
activity = await audit_logger.get_user_activity("user-123", days=30)

# Get complete history for a resource
history = await audit_logger.get_resource_history(
    AuditResource.USER, 
    "user-123"
)

# Get filtered logs
logs = await audit_logger.get_audit_logs(
    action=AuditAction.UPDATE,
    start_date=datetime(2024, 1, 1),
    limit=100
)
```

### Export Data

```python
# Export to CSV
csv_data = await audit_logger.export_audit_logs(
    format_type="csv",
    user_id="user-123"
)

# Export to Excel
excel_data = await audit_logger.export_audit_logs(
    format_type="excel",
    start_date=datetime(2024, 1, 1)
)
```

## Resource Types

The system tracks the following resource types:

- `user`: User profile information
- `user_preferences`: User volunteer preferences
- `conversation`: Chat conversations
- `message`: Individual messages
- `volunteer_match`: Volunteer opportunity matches
- `feedback`: User feedback
- `analytics_event`: System analytics events
- `system`: System-level operations

## Action Types

The system tracks these action types:

- `create`: Creating new records
- `update`: Updating existing records
- `delete`: Deleting records
- `view`: Viewing records (optional)
- `export`: Exporting data
- `login`: User login events
- `logout`: User logout events

## Diff Generation

The system automatically generates human-readable diffs for all update operations:

```
--- user_before
+++ user_after
@@ -1,4 +1,4 @@
 {
-  "email": "john@example.com",
+  "email": "john.smith@example.com",
   "first_name": "John",
-  "last_name": "Doe"
+  "last_name": "Smith"
 }
```

## Security Considerations

- Audit logs are immutable - they should never be modified once created
- Sensitive information (passwords, tokens) should not be logged in audit entries
- Access to audit logs should be restricted to authorized personnel only
- Consider implementing log rotation for long-term storage
- Ensure proper encryption for audit data at rest and in transit

## Performance Considerations

- Audit logging is asynchronous and non-blocking
- Failed audit logs don't prevent the main operation from succeeding
- Consider implementing batch writes for high-volume scenarios
- Regular cleanup of old audit logs may be necessary
- Index key fields (user_id, timestamp, resource, action) for fast queries

## Testing

Run the comprehensive test suite:

```bash
python test_audit_system.py
```

This will test all functionality including:
- Basic audit logging
- Diff generation
- Multiple resource types
- Log retrieval and filtering
- Export functionality
- Database integration

## Troubleshooting

### Common Issues

1. **Audit logs not appearing**: Check database connection and table creation
2. **Export failing**: Ensure required dependencies (openpyxl for Excel) are installed
3. **Performance issues**: Consider adding database indexes and implementing batching
4. **Large diffs**: Consider truncating very large diff outputs

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger('audit_logger').setLevel(logging.DEBUG)
```

### Database Setup

The audit tables must be created in Supabase. Run the SQL from `audit_logger.py` in the Supabase SQL editor:

```sql
-- See audit_logger.py for complete table creation SQL
CREATE TABLE IF NOT EXISTS audit_logs (...);
```

## Future Enhancements

Possible future improvements:

1. **Real-time Notifications**: Webhook/WebSocket notifications for critical changes
2. **Compliance Reports**: Pre-built reports for compliance requirements
3. **Data Retention Policies**: Automated cleanup based on retention policies
4. **Advanced Analytics**: Machine learning-based anomaly detection
5. **Integration**: Integration with external SIEM systems
6. **Bulk Operations**: More efficient handling of bulk changes

## Contributing

When adding new auditable operations:

1. Import required enums: `AuditAction`, `AuditResource`
2. Call `audit_logger.log_audit_entry()` after successful operations
3. Include relevant `old_values` and `new_values` for UPDATE operations
4. Add meaningful metadata for context
5. Test the new audit points

Example:
```python
await audit_logger.log_audit_entry(
    action=AuditAction.CREATE,
    resource=AuditResource.NEW_RESOURCE_TYPE,
    user_id=user_id,
    resource_id=new_record_id,
    new_values=record_data,
    metadata={"operation": "function_name", "source": "api"}
)
```