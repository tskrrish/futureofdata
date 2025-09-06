# KPI Email Reporting System

## Overview

The KPI Email Reporting System is an automated solution that generates and sends comprehensive volunteer analytics reports to YMCA stakeholders on scheduled intervals. This system integrates with the existing Volunteer PathFinder AI Assistant to provide actionable insights about volunteer engagement, performance metrics, and organizational impact.

## Features

### 📊 Comprehensive KPI Reporting
- **Total volunteer hours** - Aggregated across all branches and programs
- **Active volunteer count** - Deduplicated volunteer participation 
- **Member engagement rate** - YMCA member vs non-member volunteer participation
- **Branch performance analytics** - Hours and volunteer counts by location
- **Project category insights** - Performance across different volunteer activities
- **Youth Development Education (YDE) impact** - Specialized reporting for YDE programs
- **Trend analysis** - Month-over-month performance tracking

### 📧 Professional Email Templates
- **Responsive HTML design** - Optimized for desktop and mobile viewing
- **YMCA brand styling** - Consistent with organizational branding
- **Interactive charts and tables** - Easy-to-read data visualization
- **Actionable insights** - AI-generated recommendations and observations
- **Customizable filtering** - Branch-specific or organization-wide reports

### 👥 Stakeholder Management
- **Flexible recipient lists** - Support for different stakeholder groups
- **Role-based reporting** - Customized reports based on recipient responsibilities
- **Branch-specific filtering** - Branch managers receive relevant location data
- **Frequency preferences** - Daily, weekly, or monthly report cadence
- **Active/inactive controls** - Easy management of report subscriptions

### ⏰ Automated Scheduling
- **Multi-frequency support** - Daily (8 AM), Weekly (Monday 9 AM), Monthly (1st at 10 AM)
- **Background processing** - Non-blocking report generation and sending
- **Robust error handling** - Automatic retries and failure notifications
- **Manual triggering** - On-demand report generation for testing/urgent needs
- **Job management** - Add, update, delete, and monitor scheduled jobs

### 🔌 REST API Integration
- **RESTful endpoints** - Full CRUD operations for all system components
- **Authentication ready** - Designed to integrate with existing auth systems
- **Real-time monitoring** - Health checks and system status endpoints
- **Bulk operations** - Efficient handling of multiple stakeholders/reports
- **OpenAPI documentation** - Auto-generated API docs via FastAPI

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  KPI Email       │    │  KPI Scheduler  │
│                 │    │  Service         │    │                 │
│  • API Routes   │────│  • Data Analysis │────│  • Job Queue    │
│  • Request      │    │  • Template      │    │  • Background   │
│    Handling     │    │    Rendering     │    │    Processing  │
│  • Response     │    │  • SMTP Sending  │    │  • Cron Jobs    │
│    Formatting   │    │  • Stakeholder   │    │  • Error        │
└─────────────────┘    │    Management    │    │    Handling     │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Database       │    │   Email SMTP    │
                       │                  │    │                 │
                       │  • Volunteer     │    │  • Gmail/       │
                       │    Data          │    │    Corporate    │
                       │  • Analytics     │    │    Email        │
                       │  • Audit Logs    │    │  • Delivery     │
                       └──────────────────┘    │    Status       │
                                               └─────────────────┘
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- FastAPI application environment
- SMTP email account (Gmail, Office 365, etc.)
- Volunteer data in supported formats (CSV/Excel)

### Dependencies
The system requires these additional packages (already added to requirements.txt):
```bash
schedule==1.2.0
jinja2==3.1.2  # Already included
pandas==2.3.2  # Already included
```

### Email Configuration
Set up environment variables for SMTP:
```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=ymca-reports@yourorganization.org
```

For Gmail, use an App Password instead of your regular password.

### Initialization
The system automatically initializes when the FastAPI application starts:
1. KPI Email Service loads stakeholder configurations
2. Email templates are compiled and ready
3. Scheduler starts background job processing
4. API endpoints become available

## API Endpoints

### KPI Report Generation
```http
POST /api/kpi/generate-report
Content-Type: application/json

{
  "period": "current_month",  // current_month, last_month, current_week, last_week
  "branch_filter": "All"      // "All" or specific branch name
}
```

### Stakeholder Management
```http
# Get all stakeholders
GET /api/kpi/stakeholders

# Add new stakeholder  
POST /api/kpi/stakeholders
{
  "email": "director@ymca.org",
  "name": "Executive Director",
  "role": "Executive",
  "report_frequency": "weekly",
  "branches": ["all"],
  "active": true
}

# Update stakeholder
PUT /api/kpi/stakeholders/director@ymca.org
{
  "report_frequency": "monthly"
}
```

### Scheduler Management
```http
# Get scheduler status
GET /api/kpi/scheduler/status

# Run reports immediately
POST /api/kpi/scheduler/frequency/weekly/run

# Manage scheduled jobs
POST /api/kpi/scheduler/jobs
PUT /api/kpi/scheduler/jobs/{job_id}
DELETE /api/kpi/scheduler/jobs/{job_id}
```

### Send Reports
```http
# Send all reports for frequency
POST /api/kpi/send-reports/weekly
```

## Default Configuration

### Stakeholder Groups
The system comes pre-configured with these stakeholder types:
- **Executive Director** - Weekly reports, all branches
- **Volunteer Coordinator** - Daily reports, all branches  
- **Branch Managers** - Weekly reports, specific branch only
- **Program Directors** - Monthly reports, program-specific data

### Schedule Configuration
- **Daily Reports**: 8:00 AM Eastern, Monday-Friday
- **Weekly Reports**: Monday 9:00 AM Eastern  
- **Monthly Reports**: 1st of month, 10:00 AM Eastern

### Report Periods
- **Daily**: Current week data
- **Weekly**: Current week data  
- **Monthly**: Current month data

## Testing

Run the comprehensive test suite:
```bash
cd /path/to/volunteer-system
python test_kpi_system.py
```

The test suite validates:
- ✅ KPI snapshot generation
- ✅ Stakeholder management
- ✅ Email template rendering  
- ✅ Scheduler functionality
- ✅ API integration

## Usage Examples

### Adding a New Branch Manager
```python
import requests

new_stakeholder = {
    "email": "manager.blueash@ymca.org",
    "name": "Blue Ash Manager",
    "role": "Branch Management",
    "report_frequency": "weekly",
    "branches": ["Blue Ash YMCA"],
    "active": True
}

response = requests.post(
    "http://localhost:8000/api/kpi/stakeholders",
    json=new_stakeholder
)
```

### Generating On-Demand Report
```python
import requests

report_request = {
    "period": "current_month",
    "branch_filter": "Blue Ash YMCA"
}

response = requests.post(
    "http://localhost:8000/api/kpi/generate-report",
    json=report_request
)

kpi_data = response.json()
print(f"Total hours: {kpi_data['total_hours']}")
```

### Triggering Weekly Reports
```python
import requests

response = requests.post(
    "http://localhost:8000/api/kpi/send-reports/weekly"
)

result = response.json()
print(f"Reports sent: {result['sent']}")
print(f"Reports failed: {result['failed']}")
```

## Monitoring & Troubleshooting

### Health Check
```http
GET /health
```
Returns system status including KPI service readiness.

### Log Monitoring
The system logs key events:
- Report generation (success/failure)
- Email sending (delivery status)  
- Scheduler job execution
- Stakeholder management changes
- System errors and warnings

### Common Issues

**SMTP Authentication Errors**
- Verify email credentials
- Use App Passwords for Gmail
- Check firewall/network restrictions

**Missing Data in Reports**
- Validate volunteer data file path
- Check data format compatibility
- Review date range filtering

**Scheduler Not Running**
- Check background thread status
- Review job configurations
- Monitor for Python exceptions

**Template Rendering Errors**  
- Validate Jinja2 template syntax
- Check data structure compatibility
- Review HTML/CSS formatting

## Customization

### Email Templates
Edit the HTML template in `kpi_email_service.py`:
- Modify styling and branding
- Add/remove KPI metrics
- Customize layout and formatting
- Include additional charts/visualizations

### Stakeholder Categories
Add new stakeholder roles by:
1. Updating default configurations
2. Creating role-specific filtering logic  
3. Customizing report content per role

### Schedule Frequencies
Modify scheduling by:
1. Adding new frequency options
2. Updating cron expressions
3. Implementing custom timing logic

### KPI Calculations
Extend metrics by:
1. Adding new calculation methods
2. Including additional data sources
3. Creating custom aggregation logic

## Security Considerations

- **Email Credentials**: Store SMTP passwords securely using environment variables
- **API Access**: Implement authentication for production deployments
- **Data Privacy**: Ensure volunteer data complies with privacy regulations
- **Email Content**: Avoid including sensitive personal information in reports
- **Network Security**: Use TLS/SSL for email transmission

## Support

For technical support or feature requests:
1. Review this documentation
2. Check system logs for error details
3. Run test suite to validate functionality  
4. Contact system administrator with specific issues

---

**System Version**: 1.0.0  
**Last Updated**: 2025-09-06  
**Compatible With**: YMCA Volunteer PathFinder AI Assistant v1.0.0