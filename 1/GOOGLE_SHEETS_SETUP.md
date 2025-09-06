# Google Sheets Live Sync Setup Guide

## Overview
This feature enables real-time synchronization with Google Sheets, including change detection and conflict resolution for volunteer data.

## Features
- ✅ Real-time polling (30-second intervals by default)
- ✅ Change detection with checksums
- ✅ Automatic conflict resolution with multiple strategies
- ✅ Support for both Service Account and OAuth2 authentication
- ✅ Live status monitoring and error handling
- ✅ Manual sync triggers
- ✅ Comprehensive logging and statistics

## Setup Instructions

### 1. Google API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API
4. Choose your authentication method:

**Option A: API Key (for public sheets)**
- Go to "Credentials" → "Create Credentials" → "API Key"
- Copy the API key for use in the app

**Option B: OAuth2 (for private sheets)**
- Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
- Set up OAuth consent screen
- Use OAuth2 flow to get an access token with `https://www.googleapis.com/auth/spreadsheets.readonly` scope

### 2. Configure Google Sheets
**For API Key (public sheets):**
1. Make your Google Sheets document public by sharing it with "Anyone with the link can view"
2. Copy the Spreadsheet ID from the URL

**For OAuth2 (private sheets):**
1. Keep your sheet private
2. Ensure the authenticated user has access to the sheet
3. Copy the Spreadsheet ID from the URL

### 3. Application Configuration
In the app interface:
1. Enter your Spreadsheet ID
2. Specify the sheet name (default: "Sheet1")
3. Set the data range (default: "A:Z")
4. Enter either your API Key OR OAuth2 access token
5. Click "Connect to Google Sheets"

## Data Format Requirements

Your Google Sheets should have these columns (headers in first row):
- `Assignee` - Volunteer name
- `Branch` - YMCA branch location
- `Project Tag` - Project category/tag
- `Project Catalog` - Project catalog category
- `Project` - Specific project name
- `Hours` - Number of volunteer hours
- `Date` - Date of service
- `Are you a YMCA Member?` - Yes/No member status
- `Member Branch` - Branch where they are a member

## Conflict Resolution Strategies

### Latest Wins (Default)
- Uses timestamps to determine which change is newer
- Falls back to remote wins if no timestamps available

### Remote Wins
- Always accepts changes from Google Sheets
- Overwrites any local modifications

### Local Wins
- Keeps local changes and ignores remote updates
- Use with caution as it may cause data loss

### Merge Fields
- Intelligently merges fields based on data type:
  - Hours: Sums the values
  - Dates: Uses the latest date
  - Assignee/Project: Remote wins
  - Member status: Local wins

### Sum Hours
- Special strategy that sums hours when conflicts occur
- Useful for tracking total time across multiple entries

## API Reference

### LiveSyncService
```javascript
const service = new LiveSyncService({
  pollInterval: 30000,     // Sync interval in ms
  maxRetries: 3,           // Max retry attempts
  conflictStrategy: 'latest_wins'
});

await service.initialize(credentials, spreadsheetConfig);
service.startSync();
```

### useGoogleSheetsSync Hook
```javascript
const {
  data,           // Current synced data
  isConnected,    // Connection status
  isSyncing,      // Sync active status
  error,          // Last error
  changes,        // Recent changes
  conflicts,      // Detected conflicts
  connect,        // Connect function
  startSync,      // Start syncing
  triggerSync     // Manual sync
} = useGoogleSheetsSync();
```

## Monitoring and Debugging

### Status Indicators
- 🟢 Connected & Syncing - Everything working normally
- 🟡 Connected but Stopped - Connected but sync paused
- 🔴 Error - Connection or sync issues
- ⚫ Disconnected - Not connected to sheets

### Error Handling
- Automatic retry with exponential backoff
- Detailed error messages in the UI
- Sync history tracking
- Conflict resolution logging

### Performance Monitoring
- Track sync frequency and success rates
- Monitor data change volumes
- Conflict resolution statistics
- Network error tracking

## Troubleshooting

### Common Issues

**Authentication Failed**
- Verify service account JSON is complete and valid
- Check that Sheets API is enabled
- Ensure service account has access to the spreadsheet

**No Data Syncing**
- Verify spreadsheet ID is correct
- Check sheet name and range settings
- Ensure headers match expected format
- Verify data is in the specified range

**High Conflict Rates**
- Consider adjusting sync interval
- Review conflict resolution strategy
- Check for multiple users editing simultaneously
- Implement data validation in sheets

**Performance Issues**
- Reduce sync frequency for large datasets
- Limit data range to essential columns
- Consider pagination for very large sheets
- Monitor API quota usage

## Security Considerations
- Store service account credentials securely
- Use environment variables in production
- Implement proper access controls
- Regular credential rotation
- Monitor API usage and logs

## Development Notes

### Architecture
- Modular design with separate services for:
  - Google Sheets API client
  - Change detection
  - Conflict resolution
  - Live sync orchestration

### Extensibility
- Plugin system for custom conflict resolvers
- Webhook support for real-time updates
- Multiple sheet support
- Custom data transformations

### Testing
- Mock Google Sheets API for unit tests
- Integration tests with test spreadsheets
- Conflict simulation and resolution testing
- Performance testing with large datasets