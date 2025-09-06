# Data Retention Policy with Lawful Hold Mechanism

This system provides automated data retention and lawful hold capabilities for the YMCA Volunteer PathFinder application, ensuring compliance with data protection regulations while maintaining legal discovery capabilities.

## Features

### 🗄️ Data Retention Policies
- **Automated Archival**: Move old data to archive tables before permanent deletion
- **Automated Deletion**: Permanently remove data after specified retention periods
- **Configurable Categories**: Separate policies for different data types
- **Flexible Scheduling**: Daily execution with configurable time windows

### ⚖️ Lawful Hold Mechanism
- **Legal Discovery Protection**: Prevent deletion of data under legal investigation
- **Keyword Matching**: Hold data containing specific terms
- **User-Specific Holds**: Target specific users or apply system-wide
- **Expiration Management**: Automatic release of expired holds

### 📊 Monitoring & Reporting
- **Execution Logs**: Complete audit trail of all retention activities
- **Performance Metrics**: Track processed records, archive/delete counts
- **Legal Hold Tracking**: Monitor active holds and their impact
- **Automated Reports**: Weekly summaries of retention activity

## Quick Start

### 1. Database Setup
Run the SQL migration script to create required tables:

```sql
-- Execute in your Supabase SQL editor
\i setup_retention_db.sql
```

### 2. Application Integration
The retention system is automatically initialized when the application starts. Check logs for:

```
✅ Data retention system initialized
```

### 3. API Usage

#### Create a Retention Policy
```bash
curl -X POST "http://localhost:8000/api/retention/policies" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "User Data Cleanup",
    "description": "Archive inactive users after 2 years, delete after 5 years",
    "data_category": "user_profiles",
    "retention_period_days": 1825,
    "archive_after_days": 730,
    "action": "archive"
  }'
```

#### Create a Legal Hold
```bash
curl -X POST "http://localhost:8000/api/retention/legal-holds" \
  -H "Content-Type: application/json" \
  -d '{
    "case_name": "Investigation Case 2025-001",
    "description": "Hold all data related to volunteer misconduct investigation",
    "data_categories": ["user_profiles", "messages", "feedback"],
    "keywords": ["misconduct", "complaint", "incident"],
    "expires_at": "2025-12-31T23:59:59Z"
  }'
```

#### Run Retention Policies Manually
```bash
curl -X POST "http://localhost:8000/api/retention/policies/run"
```

#### Get Retention Report
```bash
curl "http://localhost:8000/api/retention/report?days=30"
```

## Data Categories

The system manages retention for these data types:

| Category | Description | Default Policy |
|----------|-------------|----------------|
| `user_profiles` | User account information | Archive after 3 years, delete after 7 years |
| `messages` | Chat conversations | Archive after 1 year, delete after 3 years |
| `analytics` | System usage analytics | Delete after 2 years |
| `feedback` | User feedback and ratings | Archive after 6 months, delete after 2 years |
| `matches` | Volunteer matching data | Delete after 1 year |
| `conversations` | Conversation metadata | Archive after 1 year, delete after 3 years |
| `preferences` | User preferences | Follows user_profiles policy |

## Retention Actions

### Archive
- Moves data to `archived_data` table with full content preservation
- Original record is deleted from production table
- Archived data includes restore deadline
- Suitable for compliance requirements with eventual deletion

### Delete
- Permanently removes data from all tables
- No recovery possible after deletion
- Suitable for analytics and temporary data
- Immediate space reclamation

### Retain
- Keeps data indefinitely (used internally for legal holds)
- Data remains in original table
- Used when legal hold prevents normal processing

## Legal Hold System

### How Legal Holds Work

1. **Creation**: Legal holds are created with specific criteria
2. **Evaluation**: During retention processing, each record is checked against active holds
3. **Protection**: Records matching hold criteria are skipped and marked as retained
4. **Expiration**: Holds automatically expire or can be manually released
5. **Cleanup**: After hold release, normal retention rules apply

### Hold Matching Criteria

Legal holds can target data using:

- **Data Categories**: Which types of data to hold
- **User IDs**: Specific users (leave empty for all users)
- **Keywords**: Text matching within data content
- **Time Range**: Hold creation and expiration dates

### Example Hold Scenarios

```python
# Investigation Hold - All data for specific users
{
    "case_name": "HR Investigation 2025-001",
    "data_categories": ["user_profiles", "messages", "feedback"],
    "user_ids": ["user-123", "user-456"],
    "expires_at": "2025-06-30T23:59:59Z"
}

# Litigation Hold - Keyword-based
{
    "case_name": "Discrimination Lawsuit",
    "data_categories": ["messages", "feedback"],
    "keywords": ["discrimination", "harassment", "unfair treatment"],
    "expires_at": "2026-12-31T23:59:59Z"
}

# Compliance Hold - All data
{
    "case_name": "Regulatory Audit",
    "data_categories": ["user_profiles", "messages", "analytics", "feedback"],
    "expires_at": "2025-09-30T23:59:59Z"
}
```

## Scheduling

The retention system runs automatically on this schedule:

| Task | Frequency | Time | Description |
|------|-----------|------|-------------|
| Retention Execution | Daily | 2:00 AM | Run all active retention policies |
| Weekly Report | Weekly | Sunday 6:00 AM | Generate activity summary |
| Legal Hold Check | Every 6 hours | 00:00, 06:00, 12:00, 18:00 | Check for expired holds |

### Manual Execution

You can trigger retention policies manually:

```python
# Run all policies
POST /api/retention/policies/run

# Run specific policy
POST /api/retention/scheduler/run-manual?policy_id=uuid

# Check scheduler status
GET /api/retention/scheduler/status
```

## Monitoring and Troubleshooting

### Health Checks

Monitor system health through these endpoints:

```bash
# Check if retention manager is available
curl "http://localhost:8000/api/retention/policies"

# View scheduler status
curl "http://localhost:8000/api/retention/scheduler/status"

# Get recent activity report
curl "http://localhost:8000/api/retention/report?days=7"
```

### Common Issues

#### Retention Manager Not Available
```
Error: "Retention manager not available"
```
**Solution**: Check Supabase connection and ensure database tables are created.

#### Scheduler Not Starting
**Symptoms**: No scheduled jobs in status endpoint
**Solution**: Check logs for scheduler initialization errors, verify APScheduler installation.

#### Legal Holds Not Working
**Symptoms**: Data being deleted despite active holds
**Solution**: Verify hold criteria match data structure, check hold status and expiration dates.

### Log Messages

Key log messages to monitor:

```
✅ Data retention system initialized
🔄 Running retention policy: Policy Name
⚖️ Legal hold applied: Case Name
❌ Error applying retention policy: Error details
```

## Security Considerations

### Access Control
- All retention tables use Row Level Security (RLS)
- Only service role can manage retention policies
- API endpoints should be protected with authentication
- Consider additional authorization for legal hold management

### Data Protection
- Archived data is encrypted at rest in Supabase
- Deletion operations are irreversible
- Legal holds provide litigation protection
- Audit trails maintain compliance records

### Compliance Features
- Complete audit trail of all retention actions
- Legal hold documentation with case references
- Automated expiration management
- Data categorization for regulatory requirements

## Performance Optimization

### Large Dataset Handling
- Retention policies process data in batches
- Database indexes optimize date-based queries
- Archive operations use efficient bulk operations
- Legal hold checks are optimized for common cases

### Monitoring Performance
```sql
-- Check retention execution performance
SELECT policy_id, AVG(records_affected), COUNT(*) as executions
FROM retention_events 
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY policy_id;

-- Monitor archive table growth
SELECT original_table, COUNT(*), 
       pg_size_pretty(pg_total_relation_size('archived_data')) as table_size
FROM archived_data 
GROUP BY original_table;
```

## API Reference

### Retention Policies

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/retention/policies` | GET | List all policies |
| `/api/retention/policies` | POST | Create new policy |
| `/api/retention/policies/run` | POST | Execute all policies |
| `/api/retention/data-categories` | GET | Get available categories |

### Legal Holds

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/retention/legal-holds` | GET | List all holds |
| `/api/retention/legal-holds` | POST | Create new hold |
| `/api/retention/legal-holds/{id}/release` | POST | Release hold |

### Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/retention/report` | GET | Activity report |
| `/api/retention/scheduler/status` | GET | Scheduler status |
| `/api/retention/scheduler/run-manual` | POST | Manual execution |

## Best Practices

### Policy Design
1. **Start Conservative**: Begin with longer retention periods and adjust based on needs
2. **Consider Dependencies**: Ensure foreign key relationships don't break
3. **Test Thoroughly**: Use test data to validate policies before production
4. **Document Policies**: Maintain clear business justification for each policy

### Legal Hold Management
1. **Document Everything**: Include detailed case information and contact details
2. **Set Expiration Dates**: Prevent indefinite holds with clear end dates
3. **Regular Review**: Periodically review active holds for relevance
4. **Coordinate with Legal**: Ensure holds meet legal requirements

### Operational Excellence
1. **Monitor Regularly**: Check retention reports and system health
2. **Backup Before Changes**: Ensure data recovery options before policy changes
3. **Test Disaster Recovery**: Verify archived data can be restored if needed
4. **Maintain Documentation**: Keep policies and procedures up to date

## Support

For issues with the data retention system:

1. Check application logs for error messages
2. Verify database connectivity and table existence
3. Review retention policy configurations
4. Check legal hold criteria and expiration dates

For questions about compliance requirements, consult with your legal and compliance teams to ensure the system meets your organization's specific needs.