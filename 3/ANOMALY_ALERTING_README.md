# YMCA Volunteer PathFinder - Anomaly Alerting System

## Overview

The Anomaly Alerting System provides proactive monitoring of volunteer activity patterns in the YMCA Volunteer PathFinder application. It detects unusual patterns in volunteer participation, hours tracking, project activity, and branch engagement, then sends intelligent alerts via Slack and email with root-cause analysis and recommended actions.

## 🚨 Key Features

### Anomaly Detection Types
- **Volunteer Drop**: Significant decreases in volunteer participation
- **Hours Spike/Drop**: Unusual increases or decreases in volunteer hours
- **Project Stall**: Projects with declining or stalled activity  
- **Branch Anomaly**: Unusual patterns in branch-specific volunteer activity
- **Category Shift**: Changes in volunteer activity distribution across categories
- **New Volunteer Plateau**: Declines in new volunteer acquisition rates

### Smart Notifications
- **Slack Integration**: Rich formatted alerts with severity colors, metrics, and actionable insights
- **Email Alerts**: HTML and plain text emails with comprehensive analysis
- **Root-Cause Hints**: AI-powered analysis suggesting potential causes
- **Recommended Actions**: Specific steps to address each anomaly type

### Advanced Features
- **Contextual Analysis**: Considers holidays, weather, academic calendars
- **Rate Limiting**: Prevents notification spam with configurable limits
- **Duplicate Suppression**: Avoids repeated alerts for the same issues
- **Severity Scoring**: Prioritizes alerts by impact and urgency
- **Historical Tracking**: Maintains alert history and trend analysis

## 📋 System Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  Volunteer Data     │───▶│  Anomaly Detection   │───▶│  Alert Generation   │
│  (Interactions,     │    │  Engine              │    │  (with Root Cause   │
│   Projects, etc.)   │    │                      │    │   Analysis)         │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                      │                           │
                                      ▼                           ▼
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  Background         │    │  Configuration       │    │  Notification       │
│  Monitoring         │    │  Management          │    │  Services           │
│  (24h cycles)       │    │                      │    │  (Slack + Email)    │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

## 🔧 Installation & Setup

### 1. Dependencies
The system is already integrated into the main application. Required packages are in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Configuration
Copy the environment template and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your notification settings:

```env
# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#alerts

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
ALERT_EMAIL_RECIPIENTS=admin1@example.com,admin2@example.com

# Detection Settings (Optional)
ANOMALY_CHECK_INTERVAL_HOURS=24
ANOMALY_LOOKBACK_DAYS=30
MAX_ALERTS_PER_HOUR=10
```

### 3. Slack Setup
1. Go to your Slack workspace
2. Create a new app or use existing one
3. Add "Incoming Webhooks" feature
4. Create a webhook for your desired channel
5. Copy the webhook URL to your `.env` file

### 4. Email Setup
For Gmail:
1. Enable 2-factor authentication
2. Generate an "App Password" for the application
3. Use the app password (not your regular password) in the configuration

## 🚀 Usage

### Automatic Monitoring
The system starts automatically when the main application launches:

```bash
python main.py
```

Anomaly detection runs every 24 hours by default, analyzing the last 30 days of data.

### Manual Detection
Trigger anomaly detection manually via the API:

```bash
curl -X GET http://localhost:8000/api/anomalies/detect
```

### API Endpoints

#### Get Anomaly Summary
```bash
GET /api/anomalies/summary?days=7
```

#### Get Anomaly History  
```bash
GET /api/anomalies/history?limit=50
```

#### Test Notifications
```bash
POST /api/anomalies/test-alert
```

#### Health Check (includes anomaly status)
```bash
GET /health
```

## 📊 Alert Examples

### Slack Alert
```
🚨 Significant Volunteer Participation Drop

Volunteer count dropped to 3 volunteers (Z-score: -3.2) on 2025-09-05

Severity: High
Type: Volunteer Drop
Affected Entities: Blue Ash, Clippard, Youth Development

🔍 Root Cause Hints:
• Holiday period detected - volunteers may be traveling
• Low YMCA member participation - focus on engagement
• Check for conflicting events or holidays

💡 Recommended Actions:
• Review volunteer engagement strategies  
• Send re-engagement emails to inactive volunteers
• Check branch-specific issues

📊 Key Metrics:
current_count: 3
expected_range: 8.5 ± 2.1
z_score: -3.2
```

### Email Alert
Rich HTML emails with:
- Color-coded severity indicators
- Detailed metrics tables
- Organized root cause analysis
- Step-by-step recommended actions
- Professional YMCA branding

## ⚙️ Configuration Options

### Detection Settings
```python
{
    "detection": {
        "enabled": True,
        "check_interval_hours": 24,
        "lookback_days": 30,
        "min_data_points": 7,
        "sensitivity_threshold": 2.0
    }
}
```

### Alert Type Configuration
```python
{
    "alert_types": {
        "volunteer_drop": {"enabled": True, "min_severity": "medium"},
        "hours_spike": {"enabled": True, "min_severity": "medium"}, 
        "hours_drop": {"enabled": True, "min_severity": "medium"},
        "project_stall": {"enabled": True, "min_severity": "high"},
        "branch_anomaly": {"enabled": True, "min_severity": "medium"},
        "category_shift": {"enabled": False, "min_severity": "low"},
        "new_volunteer_plateau": {"enabled": True, "min_severity": "high"}
    }
}
```

### Notification Filters
```python
{
    "notifications": {
        "slack": {
            "enabled": True,
            "channel": "#alerts",
            "severity_filter": ["medium", "high", "critical"]
        },
        "email": {
            "enabled": True,
            "recipients": ["admin@example.com"],
            "severity_filter": ["high", "critical"]
        }
    }
}
```

## 🧪 Testing

### Run System Verification
```bash
python verify_anomaly_system.py
```

### Run Full Test Suite (requires dependencies)
```bash
python test_anomaly_system.py
```

### Test Individual Components
```python
from anomaly_alerting import AnomalyDetector, SlackNotifier

# Test detection
detector = AnomalyDetector(volunteer_data)
alerts = detector.detect_anomalies(lookback_days=30)

# Test notifications
slack = SlackNotifier()
await slack.send_alert(alerts[0], "#test-channel")
```

## 🔍 Root Cause Analysis

The system provides intelligent analysis of anomaly causes:

### Temporal Factors
- Holiday periods (Thanksgiving, Christmas, summer breaks)
- Academic calendar transitions
- Weather-sensitive periods
- Seasonal activity patterns

### Demographic Analysis  
- Volunteer age distribution impacts
- Member vs non-member participation
- Geographic activity patterns
- Project category preferences

### Organizational Factors
- Staff availability and leadership changes
- Facility conditions and accessibility
- Policy changes and communications
- Community events and competing activities

## 📈 Monitoring & Maintenance

### Health Monitoring
Check system status:
```bash
curl http://localhost:8000/health
```

### Log Monitoring
The system logs all detection activities:
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Performance Metrics
- Detection cycle duration
- Alert generation rates
- Notification delivery success
- False positive rates

## 🛠️ Troubleshooting

### Common Issues

**No alerts being generated:**
- Check data availability and quality
- Verify detection thresholds aren't too strict
- Ensure sufficient historical data (7+ days)

**Slack notifications not working:**
- Verify webhook URL is correct
- Check webhook permissions in Slack
- Test with `POST /api/anomalies/test-alert`

**Email notifications failing:**
- Verify SMTP credentials
- Check firewall/security settings
- Test with email provider's app passwords

**Too many false positives:**
- Adjust sensitivity thresholds
- Enable duplicate suppression
- Review holiday/seasonal calendars

### Debug Mode
Enable detailed logging:
```env
DEBUG=True
```

## 🔒 Security Considerations

- Store sensitive credentials in environment variables
- Use app passwords for email authentication
- Restrict API access with proper authentication
- Monitor webhook URLs for unauthorized access
- Regular security audits of notification channels

## 📚 Advanced Usage

### Custom Anomaly Types
Extend the `AnomalyDetector` class to add custom detection logic:

```python
def _detect_custom_anomaly(self, df: pd.DataFrame) -> List[AnomalyAlert]:
    # Custom detection logic
    pass
```

### Custom Notifications
Implement additional notification channels:

```python
class CustomNotifier:
    async def send_alert(self, alert: AnomalyAlert) -> bool:
        # Custom notification logic
        pass
```

### Integration with External Systems
Connect to external monitoring tools, databases, or analytics platforms using the provided API endpoints and webhook capabilities.

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Review system logs
3. Test individual components
4. Contact the development team

## 🎯 Future Enhancements

- Machine learning-based anomaly scoring
- Predictive analytics for volunteer trends  
- Integration with calendar systems
- Mobile push notifications
- Dashboard visualizations
- Advanced statistical models