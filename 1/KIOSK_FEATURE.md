# Kiosk/Tablet Check-in Feature

This feature implements a comprehensive kiosk/tablet check-in system with offline attendance capture for the YMCA volunteer dashboard.

## Features

### Multi-Modal Check-in
- **QR Code Scanner**: Camera-based QR code scanning using device camera
- **PIN Entry**: Numeric keypad interface for PIN-based authentication
- **NFC Support**: Web NFC API integration for NFC tag reading (Chrome on Android only)

### Offline Capability
- **Local Storage**: All check-ins stored locally using browser localStorage
- **Sync Management**: Manual and automatic sync to remote server
- **Data Export**: JSON export of offline attendance data
- **Status Tracking**: Pending, synced, and error status for all entries

### Tablet-Optimized UI
- **Large Touch Targets**: Optimized for touch interaction
- **Responsive Design**: Works on various tablet sizes
- **Real-time Status**: Online/offline indicators and sync status
- **Recent Activity**: Shows last 5 check-ins with visual feedback

### Admin Features
- **Sync Manager**: Configure server endpoints and manage data sync
- **Export Tools**: Download attendance data as JSON
- **Statistics Dashboard**: View entry counts by status
- **Settings Access**: Configure kiosk behavior and sync options

## Components

### Core Components
- `KioskCheckIn`: Main kiosk interface component
- `QRScanner`: QR code scanning functionality
- `PINEntry`: PIN input interface with numeric keypad
- `NFCReader`: NFC tag reading (requires HTTPS and compatible browser)

### Support Components
- `SyncManager`: Data synchronization management
- `useOfflineAttendance`: React hook for offline data management

## Usage

### Accessing Kiosk Mode
1. From the main dashboard, click the "Kiosk Mode" button in the header
2. The interface switches to full-screen kiosk mode
3. Users can choose between QR, PIN, or NFC check-in methods

### Check-in Process
1. **QR Code**: Point device camera at volunteer's QR code
2. **PIN**: Enter 4-6 digit PIN using on-screen keypad
3. **NFC**: Tap NFC-enabled device/card to scanner area

### Data Management
1. All check-ins stored offline immediately
2. Sync to server when online (manual or automatic)
3. Export data for backup or analysis
4. Clear synced entries to save storage space

## Technical Requirements

### Browser Support
- **QR Scanner**: Modern browsers with camera access (getUserMedia)
- **NFC**: Chrome on Android with Web NFC enabled (requires HTTPS)
- **Offline Storage**: LocalStorage support (all modern browsers)

### Dependencies
- `qr-scanner`: QR code scanning library
- `qrcode-generator`: QR code generation (if needed)
- React 19+ with hooks support

### Configuration
Environment variables for server integration:
```
REACT_APP_SYNC_URL=https://api.ymca.org/attendance
REACT_APP_API_KEY=your_api_key_here
```

## Data Structure

### Attendance Entry
```json
{
  "id": "uuid",
  "timestamp": "2025-09-06T20:30:00.000Z",
  "type": "qr|pin|nfc",
  "identifier": "scanned_data_or_pin",
  "volunteerId": "volunteer_id",
  "volunteerName": "John Doe",
  "branch": "Main Branch",
  "status": "pending|synced|error",
  "checkInTime": "2025-09-06T20:30:00.000Z",
  "deviceInfo": {
    "userAgent": "...",
    "timestamp": 1725662400000,
    "online": true
  }
}
```

## Security Considerations

- All data stored locally until synced
- API key management for server communication
- HTTPS required for NFC functionality
- No sensitive data logged or stored permanently

## Future Enhancements

- Biometric authentication support
- Voice feedback for accessibility
- Multi-language support
- Advanced reporting and analytics
- Integration with existing YMCA systems
- Automatic volunteer lookup and verification