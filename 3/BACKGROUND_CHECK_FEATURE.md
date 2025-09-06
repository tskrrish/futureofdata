# Background Check Tracking Feature

## Overview

The Background Check Tracking feature provides comprehensive management of volunteer background checks, including expiration alerts and automated re-check workflows. This system ensures compliance with YMCA volunteer safety requirements and proactive management of credential renewals.

## Features

### 1. Background Check Management
- **Track Multiple Check Types**: Criminal background, reference verification, child protection training
- **Provider Integration**: Support for multiple check providers (Sterling, Checkr, Manual, etc.)
- **Status Tracking**: Complete lifecycle from submission to expiration
- **Document Storage**: JSON-based document reference storage

### 2. Expiration Alert System
- **Automated Detection**: Daily scanning for expiring checks (default: 30 days advance notice)
- **Alert Types**: 
  - `expiring_soon`: Checks expiring within warning period
  - `expired`: Checks that have passed expiration date
  - `renewal_required`: Action required alerts
  - `failed_check`: Failed check notifications
- **Multi-channel Notifications**: Volunteer and admin notification tracking

### 3. Re-check Workflows
- **Automated Workflow Initiation**: Triggered when checks approach expiration
- **Status Tracking**: From initiation to completion
- **Reminder System**: Configurable reminder intervals
- **Multiple Initiation Sources**: System automatic, admin manual, volunteer request

## Database Schema

### Core Tables

#### `background_checks`
```sql
- id: UUID (Primary Key)
- user_id: UUID (Foreign Key to users)
- volunteer_contact_id: INTEGER (Reference to volunteer system)
- check_type: VARCHAR(50) - 'background', 'reference', 'child_protection'
- check_provider: VARCHAR(100) - Provider name
- submission_date: TIMESTAMP
- completion_date: TIMESTAMP
- expiration_date: TIMESTAMP
- status: VARCHAR(20) - 'pending', 'in_progress', 'completed', 'failed', 'expired', 'renewal_required'
- result: VARCHAR(20) - 'clear', 'conditional', 'disqualified', 'pending_review'
- notes: TEXT
- documents: JSONB - Array of document references
```

#### `background_check_requirements`
```sql
- volunteer_type: VARCHAR(100) - Role-based requirements
- check_type: VARCHAR(50) - Required check type
- validity_months: INTEGER - Check validity period
- advance_warning_days: INTEGER - Days before expiration to alert
```

#### `background_check_alerts`
```sql
- background_check_id: UUID (Foreign Key)
- alert_type: VARCHAR(30)
- alert_date: TIMESTAMP
- sent_to_volunteer: BOOLEAN
- sent_to_admin: BOOLEAN
- resolved: BOOLEAN
```

#### `recheck_workflows`
```sql
- user_id: UUID (Foreign Key)
- original_check_id: UUID (Foreign Key)
- new_check_id: UUID (Foreign Key, nullable)
- workflow_status: VARCHAR(30)
- initiated_by: VARCHAR(20)
- due_date: TIMESTAMP
- completion_deadline: TIMESTAMP
- reminder_count: INTEGER
```

## API Endpoints

### Background Check Management
- `POST /api/background-checks` - Create new background check
- `GET /api/background-checks/user/{user_id}` - Get user's background checks
- `PUT /api/background-checks/{check_id}/status` - Update check status
- `GET /api/background-checks/expiring` - Get expiring checks
- `GET /api/background-checks/expired` - Get expired checks

### Alert Management
- `GET /api/background-checks/alerts` - Get alerts (pending/resolved)
- `PUT /api/background-checks/alerts/{alert_id}/resolve` - Resolve alert
- `POST /api/background-checks/process-alerts` - Manually process alerts

### Workflow Management
- `POST /api/recheck-workflows` - Initiate recheck workflow
- `GET /api/recheck-workflows/user/{user_id}` - Get user workflows
- `PUT /api/recheck-workflows/{workflow_id}/status` - Update workflow status
- `POST /api/recheck-workflows/{workflow_id}/remind` - Send workflow reminder

### Dashboard
- `GET /api/background-checks/dashboard/{user_id}` - Get dashboard statistics

## Setup Instructions

### 1. Database Setup
Run the migration script in Supabase SQL editor:
```bash
# Execute the SQL file
psql -f background_check_migration.sql
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Application
```bash
python main.py
```

### 4. Setup Scheduled Tasks
For automated alert processing:
```bash
# Run scheduler in background
python background_check_scheduler.py &

# Or run manual processing
python background_check_scheduler.py manual
```

## Usage Examples

### Creating a Background Check
```python
check_data = {
    "user_id": "user_uuid",
    "check_type": "background",
    "check_provider": "Sterling",
    "submission_date": "2024-01-15T10:00:00Z",
    "status": "pending"
}

response = await background_check_service.create_background_check(check_data)
```

### Processing Alerts
```python
# Manual alert processing
stats = await background_check_service.process_expiration_alerts()
print(f"Processed: {stats}")
```

### Initiating Workflow
```python
workflow = await background_check_service.initiate_recheck_workflow(
    user_id="user_uuid",
    original_check_id="check_uuid",
    initiated_by="admin_manual"
)
```

## Configuration

### Default Requirements
The system comes pre-configured with standard YMCA requirements:

- **Youth Mentors**: Background check (24 months), Reference check (24 months), Child protection (12 months)
- **Coaches**: Background check (24 months), Reference check (24 months)
- **Event Volunteers**: Background check (36 months)
- **General Volunteers**: Background check (36 months)

### Customization
Requirements can be modified via the `background_check_requirements` table:

```sql
UPDATE background_check_requirements 
SET validity_months = 18, advance_warning_days = 45
WHERE volunteer_type = 'youth_mentor' AND check_type = 'background';
```

## Monitoring and Maintenance

### Scheduled Tasks
- **Daily (8 AM)**: Process expiration alerts
- **Weekly (Monday 9 AM)**: Send workflow reminders
- **Monthly (1st at 2 AM)**: Cleanup old resolved alerts
- **Weekly (Friday 5 PM)**: Generate status reports

### Key Metrics
- Total background checks
- Pending/completed/expired counts
- Active workflows
- Pending alerts
- Expiring soon (30-day window)

### Troubleshooting
1. **Missing Alerts**: Check if `process_expiration_alerts()` is running daily
2. **Workflow Issues**: Verify `due_date` and `completion_deadline` calculations
3. **Database Errors**: Ensure RLS policies allow proper access
4. **Performance**: Monitor indexes on date and status columns

## Security Considerations

- **Row Level Security**: Enabled on all tables
- **Data Encryption**: Background check results should be encrypted at rest
- **Access Control**: Limit admin functions to authorized personnel
- **Audit Trail**: All status changes are tracked with timestamps
- **Document Storage**: References only - actual documents stored securely elsewhere

## Integration Points

### YMCA Volunteer System
- `volunteer_contact_id` links to existing volunteer records
- Status updates can trigger notifications in primary system

### Email Notifications
- Alert system tracks email delivery status
- Configurable templates for different alert types

### Document Management
- `documents` field stores references to external document storage
- Supports multiple document formats and providers

## Future Enhancements

1. **Email Integration**: Automated email notifications
2. **Mobile App**: Volunteer-facing mobile interface
3. **Reporting Dashboard**: Advanced analytics and reporting
4. **Integration APIs**: Connect with background check providers
5. **Bulk Operations**: Mass processing and imports
6. **Custom Workflows**: Configurable approval processes