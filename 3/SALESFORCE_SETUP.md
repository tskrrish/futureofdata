# Salesforce Nonprofit Cloud Integration

This document explains how to set up and configure the Salesforce Nonprofit Cloud integration for the YMCA Volunteer PathFinder AI Assistant.

## Features

The integration provides the following functionality:

### Contact Sync
- Syncs volunteer profiles to Salesforce Contacts
- Maps YMCA volunteer data to Nonprofit Cloud contact fields
- Handles contact deduplication by email address
- Updates volunteer skills, interests, and activity status

### Campaign Sync  
- Syncs volunteer opportunities/projects to Salesforce Campaigns
- Maps YMCA project data to campaign records
- Marks campaigns as volunteer opportunities
- Includes location, skills, and time commitment data

### Activity Sync
- Syncs volunteer interactions to Salesforce Tasks/Activities  
- Links activities to specific contacts and campaigns
- Tracks volunteer hours and activity types
- Records branch locations and activity descriptions

## Prerequisites

1. **Salesforce Nonprofit Cloud**: You need access to a Salesforce org with Nonprofit Cloud installed
2. **Connected App**: A Salesforce Connected App configured for OAuth authentication
3. **API Access**: Your Salesforce user must have API access permissions
4. **Custom Fields**: Optional custom fields for enhanced volunteer tracking

## Salesforce Setup

### 1. Create a Connected App

1. In Salesforce Setup, go to **App Manager**
2. Click **New Connected App**
3. Fill in basic information:
   - Connected App Name: "YMCA Volunteer PathFinder"
   - API Name: "YMCA_Volunteer_PathFinder"  
   - Contact Email: Your admin email
4. Enable OAuth Settings:
   - Enable OAuth Settings: ✓
   - Callback URL: `https://login.salesforce.com/`
   - Selected OAuth Scopes:
     - Access your basic information (id, profile, email, address, phone)
     - Access and manage your data (api)
     - Perform requests on your behalf at any time (refresh_token, offline_access)
5. Save the Connected App
6. Note the **Consumer Key** (Client ID) and **Consumer Secret** from the app details

### 2. Configure User Permissions

Ensure the integration user has these permissions:
- API Enabled
- View All Data (or specific object permissions)
- Modify All Data (or specific object permissions)
- Access to Contact, Campaign, and Task objects

### 3. Optional: Create Custom Fields

For enhanced volunteer tracking, consider adding these custom fields:

**Contact Object:**
- `Volunteer_Status__c` (Picklist): Active, Inactive, Pending
- `Volunteer_Skills__c` (Long Text Area): List of volunteer skills
- `Volunteer_Interests__c` (Long Text Area): Areas of interest
- `Last_Volunteer_Activity__c` (DateTime): Last volunteer activity date

**Campaign Object:**
- `Volunteer_Opportunity__c` (Checkbox): Mark as volunteer opportunity
- `Required_Skills__c` (Long Text Area): Required skills for opportunity
- `Location__c` (Text): Branch or location name
- `Time_Commitment_Hours__c` (Number): Estimated hours needed

**Task Object:**
- `Volunteer_Hours__c` (Number): Hours volunteered
- `Activity_Type__c` (Picklist): Volunteer Work, Training, Event
- `Branch_Location__c` (Text): YMCA branch location

## Environment Configuration

### 1. Environment Variables

Set the following environment variables in your deployment:

```bash
# Salesforce Configuration
SALESFORCE_INSTANCE_URL=https://your-org.my.salesforce.com
SALESFORCE_CLIENT_ID=your_consumer_key_from_connected_app
SALESFORCE_CLIENT_SECRET=your_consumer_secret_from_connected_app
SALESFORCE_USERNAME=your_salesforce_username
SALESFORCE_PASSWORD=your_salesforce_password
SALESFORCE_SECURITY_TOKEN=your_security_token
SALESFORCE_API_VERSION=v58.0

# Sync Settings
SALESFORCE_SYNC_ENABLED=true
SALESFORCE_SYNC_INTERVAL_HOURS=24
SALESFORCE_BATCH_SIZE=50
```

### 2. Getting Your Security Token

1. In Salesforce, go to **Settings** > **Reset My Security Token**
2. Click **Reset Security Token**
3. Check your email for the new security token
4. The password used for API calls is: `your_password + security_token`

### 3. Local Development

For local development, create a `.env` file:

```bash
# Copy from .env.example and fill in your values
SALESFORCE_INSTANCE_URL=https://your-dev-org.my.salesforce.com
SALESFORCE_CLIENT_ID=your_consumer_key
SALESFORCE_CLIENT_SECRET=your_consumer_secret
SALESFORCE_USERNAME=your_username@company.com
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token
SALESFORCE_SYNC_ENABLED=true
```

## API Endpoints

Once configured, the following API endpoints are available:

### GET `/api/salesforce/status`
Returns the current status of the Salesforce integration.

Response:
```json
{
  "enabled": true,
  "sync_in_progress": false,
  "last_sync_time": "2025-01-15T10:30:00Z",
  "sync_interval_hours": 24,
  "batch_size": 50,
  "needs_sync": false
}
```

### POST `/api/salesforce/test-connection`
Tests the connection to Salesforce and returns org information.

Response:
```json
{
  "connected": true,
  "instance_url": "https://your-org.my.salesforce.com",
  "api_version": "v58.0",
  "user_name": "Integration User",
  "user_email": "admin@ymca.org",
  "org_id": "00D000000000000EAA",
  "last_test": "2025-01-15T10:30:00Z"
}
```

### POST `/api/salesforce/sync`
Triggers a full sync of all volunteer data to Salesforce.

Response:
```json
{
  "success": true,
  "start_time": "2025-01-15T10:30:00Z",
  "end_time": "2025-01-15T10:35:00Z",
  "duration_seconds": 300,
  "total_processed": 150,
  "contacts": {
    "successful": 100,
    "failed": 0,
    "errors": []
  },
  "campaigns": {
    "successful": 25,
    "failed": 0,
    "errors": []
  },
  "activities": {
    "successful": 25,
    "failed": 0,
    "errors": []
  }
}
```

### POST `/api/salesforce/sync-volunteer`
Syncs a single volunteer profile to Salesforce.

Request body:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@email.com",
  "phone": "555-123-4567",
  "city": "Cincinnati",
  "state": "OH",
  "zip_code": "45202",
  "skills": "Coaching, Event Planning",
  "interests": "Youth Programs, Fitness"
}
```

### GET `/api/salesforce/data-summary`
Returns a summary of volunteer-related data in Salesforce.

Response:
```json
{
  "volunteer_contacts": 150,
  "volunteer_campaigns": 25,
  "volunteer_activities": 500,
  "retrieved_at": "2025-01-15T10:30:00Z"
}
```

## Data Mapping

### YMCA Data → Salesforce Contact
| YMCA Field | Salesforce Field | Type |
|------------|------------------|------|
| first_name | FirstName | Text |
| last_name | LastName | Text |
| email | Email | Email |
| phone | Phone | Phone |
| city | MailingCity | Text |
| state | MailingState | Text |
| zip_code | MailingPostalCode | Text |
| skills | Volunteer_Skills__c | Long Text |
| interests | Volunteer_Interests__c | Long Text |

### YMCA Project → Salesforce Campaign  
| YMCA Field | Salesforce Field | Type |
|------------|------------------|------|
| project_clean | Name | Text |
| description | Description | Long Text |
| branch_short | Location__c | Text |
| category | Required_Skills__c | Text |
| estimated_hours | Time_Commitment_Hours__c | Number |

### YMCA Interaction → Salesforce Task
| YMCA Field | Salesforce Field | Type |
|------------|------------------|------|
| project_clean | Subject | Text |
| date | ActivityDate | Date |
| hours | Volunteer_Hours__c | Number |
| branch_short | Branch_Location__c | Text |

## Monitoring and Troubleshooting

### Logs
Check application logs for sync status and error messages:
- Successful syncs are logged at INFO level
- Errors are logged at ERROR level with details
- Connection issues are logged with specific error messages

### Common Issues

1. **Authentication Failures**
   - Verify credentials and security token
   - Check if password has changed (requires new security token)
   - Ensure user has API access permissions

2. **Rate Limiting**
   - Salesforce has API call limits per org
   - The integration uses batching to minimize API calls
   - Adjust `SALESFORCE_BATCH_SIZE` if needed

3. **Field Mapping Errors**  
   - Ensure custom fields exist in Salesforce
   - Check field API names match configuration
   - Verify data types are compatible

4. **Sync Performance**
   - Large datasets may take time to sync
   - Consider running initial sync during off-peak hours
   - Monitor sync duration and adjust batch sizes

### Support

For technical support:
1. Check application logs for specific error messages
2. Test the connection using `/api/salesforce/test-connection`
3. Verify Salesforce configuration and permissions
4. Contact your Salesforce administrator for org-specific issues

## Security Considerations

- Store credentials securely using environment variables
- Use a dedicated integration user with minimal required permissions
- Regularly rotate passwords and security tokens
- Monitor API usage and access logs
- Consider IP restrictions for the Connected App in production

## Maintenance

- Review sync performance regularly
- Monitor Salesforce storage usage
- Update API version as needed
- Test integration after Salesforce releases
- Backup volunteer data before major changes