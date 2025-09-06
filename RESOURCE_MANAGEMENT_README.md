# Resource/Equipment Assignment Management System

## Overview

This system provides comprehensive resource and equipment assignment management for YMCA volunteer operations. It enables staff to track resources, assign them to shifts, monitor usage, and maintain detailed analytics.

## Features

### 🎯 Core Functionality
- **Shift Management**: Create and manage volunteer shifts with scheduling
- **Resource Inventory**: Track equipment, supplies, vehicles, and other resources
- **Assignment System**: Link resources to specific shifts with availability checking
- **Usage Tracking**: Monitor resource checkout, usage, and return
- **Analytics Dashboard**: View utilization statistics and usage trends
- **Maintenance Scheduling**: Track maintenance needs and schedules

### 📋 Key Components

#### Database Schema
- **Shifts**: Work periods that need volunteers and resources
- **Resources**: Equipment, supplies, vehicles, etc. that can be assigned
- **Resource Assignments**: Links between shifts and resources
- **Usage Logs**: Detailed tracking of resource usage
- **Maintenance Records**: Scheduling and tracking maintenance

#### API Endpoints
- `GET/POST /api/shifts` - Manage shifts
- `GET/POST /api/resources` - Manage resources  
- `GET/POST /api/assignments` - Manage resource assignments
- `PUT /api/assignments/{id}/status` - Update assignment status
- `GET /api/usage-logs` - View usage history
- `GET /api/analytics/utilization` - Get utilization statistics

#### Frontend Interface
- **Overview Tab**: Quick stats and recent activity
- **Shifts Tab**: Schedule management and shift details
- **Resources Tab**: Inventory management and resource details
- **Assignments Tab**: Create and manage resource assignments
- **Usage Tracking Tab**: Analytics and utilization reports

## Quick Start

### 1. Database Setup
Run the SQL schema to create the required tables:
```sql
-- Execute the contents of 3/shifts_resources_schema.sql in your database
```

### 2. Backend Configuration
Update your `3/config.py` with database connection details:
```python
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"
```

### 3. Install Dependencies

**Backend:**
```bash
cd 3/
pip install fastapi uvicorn supabase pandas python-multipart
```

**Frontend:**
```bash
cd 1/
npm install
```

### 4. Start the System
```bash
# Option 1: Use the startup script
python start_resource_system.py

# Option 2: Start manually
# Terminal 1 - Backend
cd 3/
uvicorn resource_api:app --reload

# Terminal 2 - Frontend  
cd 1/
npm run dev
```

### 5. Access the System
- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **Backend API**: http://localhost:8000

## Usage Guide

### Creating Resources
1. Navigate to the "Resources & Shifts" tab
2. Click "Add Resource"
3. Fill in resource details:
   - Name and description
   - Resource type (equipment, supplies, vehicle, etc.)
   - Branch location
   - Condition and maintenance schedule
   - Maximum concurrent assignments

### Creating Shifts
1. Click "Add Shift" 
2. Define shift details:
   - Name and description
   - Branch and category
   - Start/end times
   - Maximum volunteers needed

### Assigning Resources to Shifts
1. Go to the "Assignments" view
2. Click "New Assignment"
3. Select shift and resource
4. Add optional notes
5. System checks availability automatically

### Tracking Usage
1. Use status updates to track resource lifecycle:
   - **Assigned** → **Checked Out** → **In Use** → **Returned**
2. View analytics in the "Usage Tracking" tab
3. Generate utilization reports by date range

### Maintenance Management
Resources can be scheduled for maintenance with:
- Regular maintenance intervals
- Condition tracking
- Maintenance history
- Automatic scheduling

## API Examples

### Create a Resource
```javascript
POST /api/resources
{
  "name": "Pool Vacuum System",
  "description": "Professional pool cleaning equipment",
  "resource_type": "equipment",
  "branch": "Blue Ash",
  "condition": "good",
  "max_concurrent_assignments": 1
}
```

### Create a Shift  
```javascript
POST /api/shifts
{
  "name": "Morning Pool Maintenance", 
  "description": "Daily pool cleaning",
  "branch": "Blue Ash",
  "category": "Maintenance",
  "start_time": "2025-09-07T06:00:00Z",
  "end_time": "2025-09-07T08:00:00Z",
  "max_volunteers": 2
}
```

### Assign Resource to Shift
```javascript  
POST /api/assignments
{
  "shift_id": "shift-uuid-here",
  "resource_id": "resource-uuid-here", 
  "assignment_notes": "Main pool cleaning equipment"
}
```

### Update Assignment Status
```javascript
PUT /api/assignments/{assignment_id}/status
{
  "status": "checked_out",
  "condition_at_checkout": "good"
}
```

## Database Functions

The system includes useful database functions:

### Check Resource Availability
```sql
SELECT check_resource_availability(
  'resource-uuid', 
  '2025-09-07 06:00:00+00',
  '2025-09-07 08:00:00+00'
);
```

### Automatic Usage Logging
Resource assignment status changes automatically create usage log entries with:
- Timestamps
- Duration calculations  
- Condition tracking
- Action history

## Customization

### Adding Resource Types
Update the `RESOURCE_TYPES` array in `ResourceForm.jsx`:
```javascript
const RESOURCE_TYPES = [
  'equipment',
  'supplies', 
  'facility',
  'vehicle',
  'your_custom_type'
];
```

### Branch Configuration
Branches are automatically detected from existing data, or you can modify the branches list in the resource hook.

### Status Workflows
Customize assignment status flows by modifying the status update buttons in `AssignmentManager.jsx`.

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check Supabase credentials in config
   - Verify database tables exist
   - Run schema SQL scripts

2. **API Not Starting**
   - Install missing Python dependencies
   - Check port 8000 availability
   - Verify resource_api.py exists

3. **Frontend Not Loading**
   - Run `npm install` in frontend directory
   - Check Node.js version compatibility
   - Verify port 5173 availability

4. **Resource Assignment Fails**
   - Check resource availability status
   - Verify shift timing conflicts
   - Confirm max assignment limits

### Development Notes

The system is designed to extend the existing volunteer management platform with resource assignment capabilities while maintaining compatibility with existing volunteer tracking features.

## Integration

This resource management system integrates with:
- Existing volunteer data and user management
- YMCA branch structure and categories
- Current dashboard and UI patterns
- Volunteer shift scheduling (when available)

For questions or support, refer to the inline code documentation or the API documentation at `/docs` endpoint.