# Google Calendar Two-Way Sync Setup

This guide explains how to set up Google Calendar two-way synchronization for YMCA volunteer shifts.

## Features

- **Two-way sync**: Volunteer shifts sync between the YMCA system and Google Calendar
- **Per-volunteer**: Each volunteer can connect their own Google Calendar
- **Real-time updates**: Changes in either system sync to the other
- **Rich event details**: Events include project information, branch, and description
- **Conflict handling**: Smart conflict resolution for overlapping changes

## Setup Steps

### 1. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click on it and press "Enable"

### 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Configure the consent screen if prompted:
   - User Type: External (or Internal if for organization only)
   - Fill in app name: "YMCA Volunteer PathFinder"
   - Add your email as support and developer contact
   - Add scopes: `../auth/calendar` and `../auth/calendar.events`
4. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Name: "YMCA Volunteer Calendar Sync"
   - Authorized redirect URIs: 
     - `http://localhost:8000/api/calendar/callback` (for development)
     - `https://your-domain.com/api/calendar/callback` (for production)

### 3. Download Credentials

1. Click the download button next to your OAuth 2.0 Client ID
2. Save the file as `google_credentials.json` in the project root (directory 3)
3. The file should look like the `google_credentials.json.example` template

### 4. Configuration

1. Copy `config.example.py` to `config.py` if you haven't already
2. Update the configuration:

```python
# Google Calendar Integration
BASE_URL: str = 'https://your-domain.com'  # Change to your actual domain
GOOGLE_CREDENTIALS_PATH: str = 'google_credentials.json'
```

### 5. Database Setup

The Google Calendar integration requires additional database tables. Run the SQL commands from the `initialize_tables()` method in `database.py`, specifically:

- `google_calendar_auth` - Stores OAuth tokens and sync preferences
- `volunteer_shifts` - Stores volunteer shift data with calendar sync status
- `calendar_sync_log` - Logs all sync operations for debugging

### 6. Install Dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib google-auth
```

## API Endpoints

### Authentication

- `GET /api/calendar/auth-url/{user_id}` - Get OAuth authorization URL
- `GET /api/calendar/callback` - OAuth callback handler  
- `GET /api/calendar/status/{user_id}` - Check connection status
- `POST /api/calendar/disconnect/{user_id}` - Disconnect calendar

### Sync Operations

- `POST /api/calendar/sync/{user_id}` - Manual sync trigger
- `GET /api/calendar/sync-history/{user_id}` - View sync history

### Shift Management

- `POST /api/shifts` - Create new volunteer shift (auto-syncs to calendar)
- `PUT /api/shifts/{shift_id}` - Update shift (syncs changes)
- `DELETE /api/shifts/{shift_id}` - Delete shift (removes from calendar)
- `GET /api/shifts/{user_id}` - Get volunteer shifts

## Usage Flow

### For Volunteers

1. **Connect Calendar**:
   ```javascript
   // Get authorization URL
   const response = await fetch('/api/calendar/auth-url/USER_ID');
   const { auth_url } = await response.json();
   
   // Redirect user to auth_url
   window.location.href = auth_url;
   ```

2. **Check Status**:
   ```javascript
   const response = await fetch('/api/calendar/status/USER_ID');
   const status = await response.json();
   // status.connected, status.authenticated, status.sync_enabled
   ```

3. **Create Shift**:
   ```javascript
   const shiftData = {
     shift_title: "Youth Program Volunteer",
     project_name: "After School Care",
     branch: "Blue Ash YMCA",
     start_time: "2025-01-15T09:00:00Z",
     end_time: "2025-01-15T12:00:00Z",
     location: "Blue Ash YMCA",
     shift_description: "Help with after school programs"
   };
   
   const response = await fetch('/api/shifts', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify(shiftData),
     params: { user_id: 'USER_ID' }
   });
   ```

### For Administrators

1. **Manual Sync**:
   ```javascript
   const response = await fetch(`/api/calendar/sync/USER_ID`, {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ sync_direction: "bidirectional" })
   });
   ```

2. **View Sync History**:
   ```javascript
   const response = await fetch('/api/calendar/sync-history/USER_ID');
   const { sync_history } = await response.json();
   ```

## Sync Behavior

### Push to Google (YMCA → Google Calendar)
- Creates new events for unsynced shifts
- Updates existing events when shift details change
- Includes rich descriptions with project and branch info
- Sets reminders (24 hours and 30 minutes before)

### Pull from Google (Google Calendar → YMCA)
- Looks for events marked as YMCA volunteer shifts
- Creates new shifts from calendar events with YMCA metadata
- Updates shift details when calendar events change

### Bidirectional Sync
- Combines both push and pull operations
- Handles conflicts by preferring the most recently updated version
- Logs all operations for audit trail

## Event Format

Google Calendar events created by the system include:

- **Title**: "Volunteer: [Project Name]" or custom shift title
- **Description**: 
  ```
  [Custom description]
  
  Project: [Project Name]
  Branch: [Branch Name]
  
  🎯 This is a YMCA volunteer shift
  📱 Managed by YMCA Volunteer PathFinder
  ```
- **Extended Properties**: 
  - `ymca_volunteer_shift: "true"`
  - `ymca_project_id: "[ID]"`
  - `ymca_shift_id: "[ID]"`
  - `ymca_branch: "[Branch]"`

## Error Handling

The system includes comprehensive error handling:

- **Authentication errors**: Detected and reported to user
- **API rate limits**: Automatic retry with exponential backoff
- **Sync conflicts**: Logged and resolved using "last update wins"
- **Network failures**: Graceful degradation with retry logic

## Security Considerations

- OAuth tokens are stored securely in the database
- Refresh tokens are used to maintain long-term access
- Users can revoke access at any time
- All sync operations are logged for audit purposes
- Sensitive volunteer information is not exposed in calendar events

## Troubleshooting

### Common Issues

1. **"Authentication expired"**
   - User needs to reconnect their calendar
   - Check if refresh token is still valid

2. **"Sync failed"**
   - Check Google Calendar API quotas
   - Verify network connectivity
   - Review sync logs for specific errors

3. **"Events not appearing"**
   - Verify sync is enabled for the user
   - Check if events are in the correct time range
   - Confirm calendar permissions

### Debug Information

- Check `/api/calendar/sync-history/{user_id}` for detailed sync logs
- Monitor application logs for Google API errors
- Use `/api/calendar/status/{user_id}` to verify connection status

## Production Considerations

- Set up monitoring for sync failures
- Implement rate limiting to respect Google API quotas  
- Consider batch operations for bulk sync scenarios
- Set up alerts for authentication expiration
- Regular backup of sync configuration and logs