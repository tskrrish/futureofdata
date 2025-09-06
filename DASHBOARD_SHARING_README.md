# Dashboard Sharing Feature

This document describes the newly implemented shared dashboard permissions feature that allows users to share their volunteer dashboards with view-only or editor roles.

## Overview

The dashboard sharing feature enables:
- **Dashboard Creation & Management**: Save dashboard configurations with filters and settings
- **Permission-based Sharing**: Share dashboards with either view-only or editor permissions
- **Access Control**: Dashboard owners can manage who has access and what level of permissions
- **Usage Tracking**: Monitor how shared dashboards are being used

## Features

### 1. Dashboard Management
- Save current dashboard state (filters, search terms, active tab)
- Load saved dashboards
- Edit dashboard metadata (title, description, visibility)
- Delete owned dashboards

### 2. Sharing & Permissions
- **View Permission**: Users can see dashboard data but cannot modify filters or settings
- **Edit Permission**: Users can modify dashboard filters, search, and view settings
- **Owner Permission**: Full control including sharing, editing, and deleting

### 3. Public Dashboards
- Mark dashboards as public for anyone to view
- Public dashboards are read-only for non-owners

## Architecture

### Backend Components

#### Database Schema (`setup_supabase.sql`)
- `dashboards` - Stores dashboard configurations and metadata
- `dashboard_permissions` - Manages user access permissions
- `dashboard_access_logs` - Tracks dashboard usage and access patterns

#### API Endpoints (`dashboard_api.py`)
- `POST /api/dashboards` - Create new dashboard
- `GET /api/dashboards` - List user's accessible dashboards
- `GET /api/dashboards/{id}` - Get specific dashboard
- `PUT /api/dashboards/{id}` - Update dashboard (with permission check)
- `DELETE /api/dashboards/{id}` - Delete dashboard (owners only)
- `POST /api/dashboards/{id}/share` - Share dashboard with user
- `DELETE /api/dashboards/{id}/share/{user_id}` - Revoke access
- `GET /api/dashboards/{id}/permissions` - List dashboard permissions
- `GET /api/dashboards/{id}/logs` - View access logs

#### Database Integration (`database.py`)
Extended `VolunteerDatabase` class with dashboard management methods:
- Dashboard CRUD operations
- Permission management
- Access logging
- User lookup and validation

### Frontend Components

#### Dashboard Manager (`DashboardManager.jsx`)
- Dashboard list with permission indicators
- Save/Load functionality
- Delete and share actions
- Integration with sharing modal

#### Dashboard Sharing (`DashboardSharing.jsx`)
- Share dashboard with email and permission level
- View current permissions and users
- Revoke access functionality
- Permission level indicators

#### Main App Integration (`App.jsx`)
- Dashboard management bar showing current dashboard status
- Read-only mode for viewers
- Permission-based UI controls
- Modal management for dashboard operations

## Setup Instructions

### 1. Backend Setup

1. **Install Dependencies**:
   ```bash
   cd 3/
   pip install -r requirements.txt
   ```

2. **Configure Supabase**:
   - Create a Supabase project
   - Run the SQL commands from `setup_supabase.sql` in your Supabase SQL editor
   - Set environment variables:
     ```bash
     export SUPABASE_URL="your-supabase-url"
     export SUPABASE_KEY="your-supabase-anon-key"
     export SUPABASE_SERVICE_KEY="your-supabase-service-key" # Optional
     ```

3. **Start API Server**:
   ```bash
   python start_dashboard_api.py
   ```
   The API will be available at `http://localhost:8000`

### 2. Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd 1/
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm run dev
   ```
   The dashboard will be available at `http://localhost:5173`

### 3. Using the Feature

1. **Create a Dashboard**:
   - Set up your filters, search terms, and preferred tab
   - Click "Dashboard Manager" button
   - Click "Save Dashboard" and provide a title/description

2. **Share a Dashboard**:
   - In Dashboard Manager, find your dashboard
   - Click the share icon
   - Enter user's email and select permission level (view/edit)
   - Click "Share Dashboard"

3. **Access Shared Dashboards**:
   - Shared dashboards appear in your Dashboard Manager
   - Permission level is displayed next to each dashboard
   - Load any accessible dashboard by clicking the folder icon

## Permission Levels Explained

### Owner
- Full access to dashboard
- Can edit all settings and data
- Can share with others
- Can delete dashboard
- Can view access logs

### Editor
- Can modify filters and search terms
- Can change active tab
- Cannot share with others
- Cannot delete dashboard
- Cannot access sharing settings

### Viewer
- Can view all dashboard data and charts
- Cannot modify any settings or filters
- Read-only access to all functionality
- Controls are disabled with "(Read Only)" indicators

## Security Features

- **Row Level Security (RLS)**: Enforced at database level
- **JWT Authentication**: API endpoints require valid tokens
- **Permission Validation**: All operations check user permissions
- **Access Logging**: All dashboard interactions are logged
- **Owner-only Operations**: Sharing and deletion restricted to owners

## API Authentication

Currently uses a simple token-based approach where the JWT token contains the user ID. In production, implement proper JWT validation with:

1. Token signature verification
2. Expiration checking
3. User session validation
4. Proper user context extraction

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify Supabase URL and keys are correct
   - Check if Supabase project is active
   - Ensure RLS policies are properly configured

2. **Permission Denied Errors**:
   - Verify user has correct permissions for the operation
   - Check if dashboard exists and is accessible
   - Ensure proper authentication token is provided

3. **Frontend API Connection**:
   - Verify API server is running on port 8000
   - Check CORS settings if accessing from different domain
   - Ensure authentication token is properly stored/retrieved

### Development Notes

- The current implementation uses a simplified authentication system
- In production, integrate with proper user authentication (OAuth, JWT, etc.)
- Consider implementing real-time updates for shared dashboard changes
- Add notification system for sharing events
- Implement dashboard templates and cloning functionality

## Future Enhancements

1. **Real-time Collaboration**: Live updates when multiple users view same dashboard
2. **Comment System**: Add comments and discussions on dashboards
3. **Version History**: Track dashboard changes over time
4. **Export Sharing**: Share dashboards as PDFs or images
5. **Dashboard Templates**: Create reusable dashboard templates
6. **Advanced Permissions**: Granular permissions for specific dashboard elements
7. **Integration APIs**: Allow external systems to create/update dashboards
8. **Mobile App**: Mobile-friendly dashboard sharing interface

This dashboard sharing feature provides a robust foundation for collaborative data analysis while maintaining proper security and access controls.