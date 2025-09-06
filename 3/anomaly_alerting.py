"""
Anomaly Alerting System for YMCA Volunteer Management
Proactive Slack/email alerts with root-cause hints
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from scipy import stats
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import os
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    VOLUNTEER_DROP = "volunteer_drop"
    HOURS_SPIKE = "hours_spike"
    HOURS_DROP = "hours_drop"
    PROJECT_STALL = "project_stall"
    BRANCH_ANOMALY = "branch_anomaly"
    CATEGORY_SHIFT = "category_shift"
    NEW_VOLUNTEER_PLATEAU = "new_volunteer_plateau"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AnomalyAlert:
    anomaly_type: AnomalyType
    severity: AlertSeverity
    title: str
    description: str
    root_cause_hints: List[str]
    affected_entities: List[str]  # branches, projects, volunteers
    metrics: Dict[str, Any]
    timestamp: datetime
    recommended_actions: List[str]

class AnomalyDetector:
    """Core anomaly detection logic"""
    
    def __init__(self, volunteer_data: Dict[str, Any]):
        self.volunteer_data = volunteer_data
        self.interactions_df = volunteer_data.get('interactions', pd.DataFrame())
        self.volunteers_df = volunteer_data.get('volunteers', pd.DataFrame())
        self.projects_df = volunteer_data.get('projects', pd.DataFrame())
        
    def detect_anomalies(self, lookback_days: int = 30) -> List[AnomalyAlert]:
        """Main anomaly detection method"""
        alerts = []
        
        if self.interactions_df.empty:
            logger.warning("No interaction data available for anomaly detection")
            return alerts
        
        try:
            # Prepare time-series data
            df = self._prepare_timeseries_data(lookback_days)
            
            # Run different anomaly detection checks
            alerts.extend(self._detect_volunteer_drop_anomalies(df))
            alerts.extend(self._detect_hours_anomalies(df))
            alerts.extend(self._detect_project_stall_anomalies(df))
            alerts.extend(self._detect_branch_anomalies(df))
            alerts.extend(self._detect_category_shift_anomalies(df))
            alerts.extend(self._detect_new_volunteer_plateau(df))
            
            # Sort by severity and timestamp
            alerts.sort(key=lambda x: (x.severity.value, x.timestamp), reverse=True)
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            
        return alerts
    
    def _prepare_timeseries_data(self, lookback_days: int) -> pd.DataFrame:
        """Prepare time-series data for analysis"""
        df = self.interactions_df.copy()
        
        # Convert date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            
            # Filter to lookback period
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            df = df[df['date'] >= cutoff_date]
        
        # Ensure numeric columns
        df['hours'] = pd.to_numeric(df.get('hours', 0), errors='coerce').fillna(0)
        df['pledged'] = pd.to_numeric(df.get('pledged', 0), errors='coerce').fillna(0)
        
        return df
    
    def _detect_volunteer_drop_anomalies(self, df: pd.DataFrame) -> List[AnomalyAlert]:
        """Detect sudden drops in volunteer participation"""
        alerts = []
        
        try:
            # Group by date and count unique volunteers
            daily_volunteers = df.groupby('date')['contact_id'].nunique().reset_index()
            daily_volunteers.columns = ['date', 'volunteer_count']
            
            if len(daily_volunteers) < 7:  # Need at least a week of data
                return alerts
            
            # Calculate rolling average and standard deviation
            daily_volunteers['rolling_mean'] = daily_volunteers['volunteer_count'].rolling(7).mean()
            daily_volunteers['rolling_std'] = daily_volunteers['volunteer_count'].rolling(7).std()
            
            # Detect significant drops (2+ standard deviations below mean)
            recent_data = daily_volunteers.tail(3)  # Last 3 days
            
            for _, row in recent_data.iterrows():
                if pd.notna(row['rolling_mean']) and pd.notna(row['rolling_std']):
                    z_score = (row['volunteer_count'] - row['rolling_mean']) / max(row['rolling_std'], 1)
                    
                    if z_score < -2.0:  # Significant drop
                        severity = AlertSeverity.HIGH if z_score < -3.0 else AlertSeverity.MEDIUM
                        
                        # Identify affected branches
                        day_data = df[df['date'] == row['date']]
                        active_branches = day_data['branch_short'].value_counts()
                        
                        root_causes = [
                            "Potential seasonal decline in volunteer activity",
                            "Check for conflicting events or holidays",
                            "Review recent communication or policy changes",
                            "Verify data collection accuracy"
                        ]
                        
                        if len(active_branches) < 3:
                            root_causes.append("Limited branch participation - focus on outreach")
                        
                        alerts.append(AnomalyAlert(
                            anomaly_type=AnomalyType.VOLUNTEER_DROP,
                            severity=severity,
                            title=f"Significant Drop in Volunteer Participation",
                            description=f"Volunteer count dropped to {row['volunteer_count']} (Z-score: {z_score:.2f}) on {row['date'].strftime('%Y-%m-%d')}",
                            root_cause_hints=root_causes,
                            affected_entities=active_branches.index.tolist()[:5],
                            metrics={
                                "current_count": int(row['volunteer_count']),
                                "expected_range": f"{row['rolling_mean']:.1f} ± {row['rolling_std']:.1f}",
                                "z_score": float(z_score),
                                "date": row['date'].strftime('%Y-%m-%d')
                            },
                            timestamp=datetime.now(),
                            recommended_actions=[
                                "Review volunteer engagement strategies",
                                "Send re-engagement emails to inactive volunteers",
                                "Check branch-specific issues",
                                "Plan volunteer appreciation events"
                            ]
                        ))
        
        except Exception as e:
            logger.error(f"Error detecting volunteer drop anomalies: {e}")
        
        return alerts
    
    def _detect_hours_anomalies(self, df: pd.DataFrame) -> List[AnomalyAlert]:
        """Detect unusual patterns in volunteer hours"""
        alerts = []
        
        try:
            # Daily total hours
            daily_hours = df.groupby('date').agg({
                'hours': 'sum',
                'pledged': 'sum'
            }).reset_index()
            
            if len(daily_hours) < 7:
                return alerts
            
            # Use pledged hours if available, otherwise use hours
            hours_col = 'pledged' if daily_hours['pledged'].sum() > 0 else 'hours'
            
            # Calculate rolling statistics
            daily_hours['rolling_mean'] = daily_hours[hours_col].rolling(7).mean()
            daily_hours['rolling_std'] = daily_hours[hours_col].rolling(7).std()
            
            # Detect spikes and drops
            recent_data = daily_hours.tail(3)
            
            for _, row in recent_data.iterrows():
                if pd.notna(row['rolling_mean']) and pd.notna(row['rolling_std']):
                    z_score = (row[hours_col] - row['rolling_mean']) / max(row['rolling_std'], 1)
                    
                    if abs(z_score) > 2.5:
                        anomaly_type = AnomalyType.HOURS_SPIKE if z_score > 0 else AnomalyType.HOURS_DROP
                        severity = AlertSeverity.HIGH if abs(z_score) > 3.5 else AlertSeverity.MEDIUM
                        
                        direction = "spike" if z_score > 0 else "drop"
                        
                        # Analyze contributing factors
                        day_data = df[df['date'] == row['date']]
                        top_projects = day_data.groupby('project_clean')[hours_col].sum().sort_values(ascending=False).head(3)
                        top_branches = day_data.groupby('branch_short')[hours_col].sum().sort_values(ascending=False).head(3)
                        
                        root_causes = [
                            f"Unusual {hours_col} {direction} detected",
                            "Check for special events or seasonal activities",
                            "Verify data entry accuracy",
                            "Review project scheduling changes"
                        ]
                        
                        if z_score > 0:
                            root_causes.extend([
                                "Possible large event or group activity",
                                "New volunteer orientation session"
                            ])
                        else:
                            root_causes.extend([
                                "Potential volunteer scheduling conflicts",
                                "Weather or external factors affecting participation"
                            ])
                        
                        alerts.append(AnomalyAlert(
                            anomaly_type=anomaly_type,
                            severity=severity,
                            title=f"Volunteer Hours {direction.title()} Detected",
                            description=f"Total {hours_col} showed a {direction} to {row[hours_col]:.1f} (Z-score: {z_score:.2f}) on {row['date'].strftime('%Y-%m-%d')}",
                            root_cause_hints=root_causes,
                            affected_entities=list(top_projects.index) + list(top_branches.index),
                            metrics={
                                "current_hours": float(row[hours_col]),
                                "expected_range": f"{row['rolling_mean']:.1f} ± {row['rolling_std']:.1f}",
                                "z_score": float(z_score),
                                "top_projects": top_projects.to_dict(),
                                "top_branches": top_branches.to_dict()
                            },
                            timestamp=datetime.now(),
                            recommended_actions=[
                                "Investigate contributing projects/branches",
                                "Validate data entry procedures",
                                "Check for system recording errors",
                                "Review volunteer scheduling systems"
                            ]
                        ))
        
        except Exception as e:
            logger.error(f"Error detecting hours anomalies: {e}")
        
        return alerts
    
    def _detect_project_stall_anomalies(self, df: pd.DataFrame) -> List[AnomalyAlert]:
        """Detect projects with stalled or declining activity"""
        alerts = []
        
        try:
            # Group by project and analyze activity trends
            project_activity = df.groupby(['project_id', 'project_clean', 'date']).agg({
                'hours': 'sum',
                'pledged': 'sum',
                'contact_id': 'nunique'
            }).reset_index()
            
            # For each project, check recent activity vs historical
            for project_id in project_activity['project_id'].unique():
                if pd.isna(project_id):
                    continue
                    
                project_data = project_activity[project_activity['project_id'] == project_id].sort_values('date')
                
                if len(project_data) < 10:  # Need sufficient history
                    continue
                
                # Check if recent activity is significantly lower
                recent_activity = project_data.tail(5)['hours'].mean()
                historical_activity = project_data.head(-5)['hours'].mean() if len(project_data) > 10 else project_data['hours'].mean()
                
                if historical_activity > 0:
                    decline_ratio = (historical_activity - recent_activity) / historical_activity
                    
                    if decline_ratio > 0.7:  # 70% decline
                        project_name = project_data.iloc[0]['project_clean']
                        severity = AlertSeverity.HIGH if decline_ratio > 0.9 else AlertSeverity.MEDIUM
                        
                        alerts.append(AnomalyAlert(
                            anomaly_type=AnomalyType.PROJECT_STALL,
                            severity=severity,
                            title=f"Project Activity Decline: {project_name}",
                            description=f"Project '{project_name}' shows {decline_ratio*100:.1f}% decline in recent activity",
                            root_cause_hints=[
                                "Project may be reaching completion",
                                "Seasonal or scheduling factors",
                                "Volunteer interest waning",
                                "Resource or leadership constraints",
                                "Check project status and requirements"
                            ],
                            affected_entities=[project_name],
                            metrics={
                                "project_id": int(project_id),
                                "decline_ratio": float(decline_ratio),
                                "recent_hours": float(recent_activity),
                                "historical_hours": float(historical_activity)
                            },
                            timestamp=datetime.now(),
                            recommended_actions=[
                                "Contact project coordinators",
                                "Review project status and needs",
                                "Consider volunteer re-engagement strategies",
                                "Evaluate project completion timeline"
                            ]
                        ))
        
        except Exception as e:
            logger.error(f"Error detecting project stall anomalies: {e}")
        
        return alerts
    
    def _detect_branch_anomalies(self, df: pd.DataFrame) -> List[AnomalyAlert]:
        """Detect unusual patterns in branch activity"""
        alerts = []
        
        try:
            # Analyze branch activity patterns
            branch_daily = df.groupby(['branch_short', 'date']).agg({
                'hours': 'sum',
                'contact_id': 'nunique'
            }).reset_index()
            
            for branch in df['branch_short'].unique():
                if pd.isna(branch) or branch == '':
                    continue
                    
                branch_data = branch_daily[branch_daily['branch_short'] == branch]
                
                if len(branch_data) < 7:
                    continue
                
                # Calculate branch activity metrics
                recent_volunteers = branch_data.tail(7)['contact_id'].mean()
                historical_volunteers = branch_data.head(-7)['contact_id'].mean() if len(branch_data) > 14 else branch_data['contact_id'].mean()
                
                if historical_volunteers > 0:
                    volunteer_change = (recent_volunteers - historical_volunteers) / historical_volunteers
                    
                    if abs(volunteer_change) > 0.5:  # 50% change
                        direction = "increase" if volunteer_change > 0 else "decrease"
                        severity = AlertSeverity.MEDIUM if abs(volunteer_change) < 0.8 else AlertSeverity.HIGH
                        
                        alerts.append(AnomalyAlert(
                            anomaly_type=AnomalyType.BRANCH_ANOMALY,
                            severity=severity,
                            title=f"Branch Activity {direction.title()}: {branch}",
                            description=f"Branch '{branch}' shows {abs(volunteer_change)*100:.1f}% {direction} in volunteer participation",
                            root_cause_hints=[
                                f"Branch-specific factors affecting {direction}",
                                "Local events or community changes",
                                "Staffing or leadership changes",
                                "Facility or program modifications",
                                "Marketing or outreach effectiveness"
                            ],
                            affected_entities=[branch],
                            metrics={
                                "branch": branch,
                                "change_ratio": float(volunteer_change),
                                "recent_avg_volunteers": float(recent_volunteers),
                                "historical_avg_volunteers": float(historical_volunteers)
                            },
                            timestamp=datetime.now(),
                            recommended_actions=[
                                f"Contact {branch} branch leadership",
                                "Investigate branch-specific factors",
                                "Review recent branch communications",
                                "Assess facility or program changes"
                            ]
                        ))
        
        except Exception as e:
            logger.error(f"Error detecting branch anomalies: {e}")
        
        return alerts
    
    def _detect_category_shift_anomalies(self, df: pd.DataFrame) -> List[AnomalyAlert]:
        """Detect shifts in volunteer activity categories"""
        alerts = []
        
        try:
            # Compare recent vs historical category distributions
            recent_data = df.tail(100)  # Recent activities
            historical_data = df.head(-100) if len(df) > 200 else df
            
            recent_categories = recent_data['project_category'].value_counts(normalize=True)
            historical_categories = historical_data['project_category'].value_counts(normalize=True)
            
            # Find significant shifts
            for category in set(recent_categories.index) | set(historical_categories.index):
                recent_pct = recent_categories.get(category, 0)
                historical_pct = historical_categories.get(category, 0)
                
                if historical_pct > 0.1:  # Only consider categories with >10% historical share
                    change = (recent_pct - historical_pct) / historical_pct
                    
                    if abs(change) > 0.5:  # 50% change
                        direction = "increase" if change > 0 else "decrease"
                        severity = AlertSeverity.MEDIUM
                        
                        alerts.append(AnomalyAlert(
                            anomaly_type=AnomalyType.CATEGORY_SHIFT,
                            severity=severity,
                            title=f"Category Activity Shift: {category}",
                            description=f"Category '{category}' shows {abs(change)*100:.1f}% {direction} in volunteer activity share",
                            root_cause_hints=[
                                "Seasonal program changes",
                                "New initiatives or campaigns",
                                "Volunteer preference shifts",
                                "Program availability changes",
                                "Community needs evolution"
                            ],
                            affected_entities=[category],
                            metrics={
                                "category": category,
                                "change_ratio": float(change),
                                "recent_share": float(recent_pct),
                                "historical_share": float(historical_pct)
                            },
                            timestamp=datetime.now(),
                            recommended_actions=[
                                "Review category program offerings",
                                "Assess volunteer training needs",
                                "Check community demand patterns",
                                "Consider resource reallocation"
                            ]
                        ))
        
        except Exception as e:
            logger.error(f"Error detecting category shift anomalies: {e}")
        
        return alerts
    
    def _detect_new_volunteer_plateau(self, df: pd.DataFrame) -> List[AnomalyAlert]:
        """Detect plateaus in new volunteer acquisition"""
        alerts = []
        
        try:
            # Track first-time volunteers by date
            volunteer_first_dates = df.groupby('contact_id')['date'].min().reset_index()
            daily_new_volunteers = volunteer_first_dates.groupby('date').size().reset_index(name='new_volunteers')
            
            if len(daily_new_volunteers) < 14:  # Need at least 2 weeks
                return alerts
            
            # Check for plateau in new volunteer acquisition
            recent_new = daily_new_volunteers.tail(7)['new_volunteers'].mean()
            historical_new = daily_new_volunteers.head(-7)['new_volunteers'].mean()
            
            if historical_new > recent_new and historical_new > 1:  # Declining new volunteer rate
                decline_ratio = (historical_new - recent_new) / historical_new
                
                if decline_ratio > 0.4:  # 40% decline
                    severity = AlertSeverity.HIGH if decline_ratio > 0.7 else AlertSeverity.MEDIUM
                    
                    alerts.append(AnomalyAlert(
                        anomaly_type=AnomalyType.NEW_VOLUNTEER_PLATEAU,
                        severity=severity,
                        title="New Volunteer Acquisition Decline",
                        description=f"New volunteer acquisition rate has declined by {decline_ratio*100:.1f}%",
                        root_cause_hints=[
                            "Recruitment efforts may need refreshing",
                            "Seasonal factors affecting sign-ups",
                            "Marketing campaign effectiveness declining",
                            "Onboarding process barriers",
                            "Community awareness levels"
                        ],
                        affected_entities=["Recruitment", "Onboarding"],
                        metrics={
                            "decline_ratio": float(decline_ratio),
                            "recent_avg_new": float(recent_new),
                            "historical_avg_new": float(historical_new)
                        },
                        timestamp=datetime.now(),
                        recommended_actions=[
                            "Review recruitment strategies",
                            "Enhance marketing campaigns",
                            "Simplify onboarding process",
                            "Increase community outreach",
                            "Partner with local organizations"
                        ]
                    ))
        
        except Exception as e:
            logger.error(f"Error detecting new volunteer plateau: {e}")
        
        return alerts


class SlackNotifier:
    """Slack notification service for anomaly alerts"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        
    async def send_alert(self, alert: AnomalyAlert, channel: str = "#alerts") -> bool:
        """Send anomaly alert to Slack"""
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        try:
            # Format severity color
            color_map = {
                AlertSeverity.LOW: "#36a64f",
                AlertSeverity.MEDIUM: "#ff9500", 
                AlertSeverity.HIGH: "#ff4500",
                AlertSeverity.CRITICAL: "#ff0000"
            }
            
            # Build Slack message
            attachment = {
                "color": color_map.get(alert.severity, "#cccccc"),
                "title": f"🚨 {alert.title}",
                "text": alert.description,
                "fields": [
                    {
                        "title": "Severity",
                        "value": alert.severity.value.title(),
                        "short": True
                    },
                    {
                        "title": "Type",
                        "value": alert.anomaly_type.value.replace('_', ' ').title(),
                        "short": True
                    },
                    {
                        "title": "Affected Entities",
                        "value": ", ".join(alert.affected_entities[:5]),
                        "short": False
                    }
                ],
                "footer": "YMCA Volunteer PathFinder",
                "ts": int(alert.timestamp.timestamp())
            }
            
            # Add root cause hints
            if alert.root_cause_hints:
                hints_text = "\n".join([f"• {hint}" for hint in alert.root_cause_hints[:3]])
                attachment["fields"].append({
                    "title": "🔍 Root Cause Hints",
                    "value": hints_text,
                    "short": False
                })
            
            # Add recommended actions
            if alert.recommended_actions:
                actions_text = "\n".join([f"• {action}" for action in alert.recommended_actions[:3]])
                attachment["fields"].append({
                    "title": "💡 Recommended Actions",
                    "value": actions_text,
                    "short": False
                })
            
            # Add key metrics
            if alert.metrics:
                metrics_items = []
                for key, value in list(alert.metrics.items())[:4]:
                    if isinstance(value, (int, float)):
                        metrics_items.append(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
                    else:
                        metrics_items.append(f"{key}: {value}")
                
                if metrics_items:
                    attachment["fields"].append({
                        "title": "📊 Key Metrics",
                        "value": "\n".join(metrics_items),
                        "short": False
                    })
            
            payload = {
                "channel": channel,
                "username": "YMCA Anomaly Bot",
                "icon_emoji": ":warning:",
                "attachments": [attachment]
            }
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent successfully: {alert.title}")
                return True
            else:
                logger.error(f"Slack alert failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False
    
    async def send_summary_report(self, alerts: List[AnomalyAlert], channel: str = "#alerts") -> bool:
        """Send a summary report of multiple alerts"""
        if not alerts:
            return True
            
        try:
            severity_counts = {}
            for alert in alerts:
                severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            
            summary_text = f"📋 *Anomaly Detection Summary* - {len(alerts)} alerts detected"
            severity_text = ", ".join([f"{count} {severity}" for severity, count in severity_counts.items()])
            
            attachment = {
                "color": "#ff9500",
                "title": "YMCA Volunteer System - Anomaly Report",
                "text": f"{summary_text}\n*Severity breakdown:* {severity_text}",
                "fields": [],
                "footer": "YMCA Volunteer PathFinder",
                "ts": int(datetime.now().timestamp())
            }
            
            # Add top alerts
            for i, alert in enumerate(alerts[:5]):
                attachment["fields"].append({
                    "title": f"{i+1}. {alert.title}",
                    "value": f"*Severity:* {alert.severity.value.title()}\n*Description:* {alert.description}",
                    "short": False
                })
            
            payload = {
                "channel": channel,
                "username": "YMCA Anomaly Bot",
                "icon_emoji": ":clipboard:",
                "attachments": [attachment]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending Slack summary: {e}")
            return False


class EmailNotifier:
    """Email notification service for anomaly alerts"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        
    async def send_alert(self, alert: AnomalyAlert, recipients: List[str]) -> bool:
        """Send anomaly alert via email"""
        if not all([self.smtp_username, self.smtp_password]):
            logger.warning("Email credentials not configured")
            return False
        
        try:
            msg = MimeMultipart('alternative')
            msg['Subject'] = f"🚨 YMCA Volunteer Alert: {alert.title}"
            msg['From'] = self.from_email
            msg['To'] = ", ".join(recipients)
            
            # Create HTML email content
            html_content = self._create_html_alert(alert)
            html_part = MimeText(html_content, 'html')
            
            # Create plain text version
            text_content = self._create_text_alert(alert)
            text_part = MimeText(text_content, 'plain')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent successfully: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False
    
    def _create_html_alert(self, alert: AnomalyAlert) -> str:
        """Create HTML email content for alert"""
        severity_colors = {
            AlertSeverity.LOW: "#28a745",
            AlertSeverity.MEDIUM: "#ffc107",
            AlertSeverity.HIGH: "#fd7e14", 
            AlertSeverity.CRITICAL: "#dc3545"
        }
        
        color = severity_colors.get(alert.severity, "#6c757d")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="border-left: 5px solid {color}; padding-left: 20px; margin-bottom: 20px;">
                <h2 style="color: {color}; margin-top: 0;">🚨 {alert.title}</h2>
                <p style="font-size: 16px; color: #333;">{alert.description}</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #495057; margin-top: 0;">Alert Details</h3>
                <ul style="color: #6c757d;">
                    <li><strong>Severity:</strong> {alert.severity.value.title()}</li>
                    <li><strong>Type:</strong> {alert.anomaly_type.value.replace('_', ' ').title()}</li>
                    <li><strong>Timestamp:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>Affected Entities:</strong> {', '.join(alert.affected_entities[:5])}</li>
                </ul>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h3 style="color: #495057;">🔍 Root Cause Hints</h3>
                <ul style="color: #6c757d;">
        """
        
        for hint in alert.root_cause_hints:
            html += f"<li>{hint}</li>"
        
        html += """
                </ul>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h3 style="color: #495057;">💡 Recommended Actions</h3>
                <ol style="color: #6c757d;">
        """
        
        for action in alert.recommended_actions:
            html += f"<li>{action}</li>"
        
        html += """
                </ol>
            </div>
        """
        
        if alert.metrics:
            html += """
            <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px;">
                <h3 style="color: #495057; margin-top: 0;">📊 Key Metrics</h3>
                <table style="width: 100%; border-collapse: collapse;">
            """
            
            for key, value in alert.metrics.items():
                html += f"""
                    <tr>
                        <td style="padding: 5px; border-bottom: 1px solid #dee2e6; font-weight: bold;">{key}:</td>
                        <td style="padding: 5px; border-bottom: 1px solid #dee2e6;">{value}</td>
                    </tr>
                """
            
            html += """
                </table>
            </div>
            """
        
        html += """
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
            <p style="color: #6c757d; font-size: 14px;">
                This alert was generated by the YMCA Volunteer PathFinder Anomaly Detection System.<br>
                For questions or to update notification preferences, contact your system administrator.
            </p>
        </body>
        </html>
        """
        
        return html
    
    def _create_text_alert(self, alert: AnomalyAlert) -> str:
        """Create plain text email content for alert"""
        text = f"""
🚨 YMCA VOLUNTEER ALERT: {alert.title}

DESCRIPTION:
{alert.description}

ALERT DETAILS:
- Severity: {alert.severity.value.title()}
- Type: {alert.anomaly_type.value.replace('_', ' ').title()}
- Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- Affected Entities: {', '.join(alert.affected_entities[:5])}

🔍 ROOT CAUSE HINTS:
"""
        
        for i, hint in enumerate(alert.root_cause_hints, 1):
            text += f"{i}. {hint}\n"
        
        text += "\n💡 RECOMMENDED ACTIONS:\n"
        
        for i, action in enumerate(alert.recommended_actions, 1):
            text += f"{i}. {action}\n"
        
        if alert.metrics:
            text += "\n📊 KEY METRICS:\n"
            for key, value in alert.metrics.items():
                text += f"- {key}: {value}\n"
        
        text += """
---
This alert was generated by the YMCA Volunteer PathFinder Anomaly Detection System.
For questions or to update notification preferences, contact your system administrator.
        """
        
        return text


class RootCauseAnalyzer:
    """Advanced root cause analysis for anomaly alerts"""
    
    def __init__(self, volunteer_data: Dict[str, Any]):
        self.volunteer_data = volunteer_data
        self.interactions_df = volunteer_data.get('interactions', pd.DataFrame())
        
    def analyze_volunteer_drop_causes(self, alert: AnomalyAlert, df: pd.DataFrame) -> List[str]:
        """Analyze potential causes for volunteer participation drops"""
        causes = alert.root_cause_hints.copy()
        
        try:
            # Analyze temporal patterns
            date_str = alert.metrics.get('date')
            if date_str:
                alert_date = pd.to_datetime(date_str)
                
                # Check if it's a holiday period
                if self._is_holiday_period(alert_date):
                    causes.append("Holiday period detected - volunteers may be traveling or busy with family")
                
                # Check weather impact (if location data available)
                if self._is_weather_sensitive_period(alert_date):
                    causes.append("Weather-sensitive period - check for severe weather conditions")
                
                # Check academic calendar impact
                if self._is_academic_transition_period(alert_date):
                    causes.append("Academic transition period - student volunteers may be affected")
            
            # Analyze affected demographics
            recent_data = df.tail(50)  # Recent activity
            if not recent_data.empty:
                age_dist = recent_data.get('age', pd.Series()).dropna()
                if len(age_dist) > 0:
                    avg_age = age_dist.mean()
                    if avg_age > 55:
                        causes.append("Older volunteer demographic - check accessibility and health considerations")
                    elif avg_age < 25:
                        causes.append("Younger volunteer demographic - check work/study schedule conflicts")
                
                # Check member vs non-member impact
                member_ratio = recent_data.get('is_ymca_member', pd.Series()).mean()
                if member_ratio < 0.3:
                    causes.append("Low YMCA member participation - focus on member engagement programs")
            
        except Exception as e:
            logger.error(f"Error in volunteer drop cause analysis: {e}")
        
        return causes
    
    def analyze_hours_anomaly_causes(self, alert: AnomalyAlert, df: pd.DataFrame) -> List[str]:
        """Analyze causes for hours spikes or drops"""
        causes = alert.root_cause_hints.copy()
        
        try:
            metrics = alert.metrics
            top_projects = metrics.get('top_projects', {})
            top_branches = metrics.get('top_branches', {})
            
            # Analyze project concentration
            if top_projects and len(top_projects) == 1:
                project_name = list(top_projects.keys())[0]
                causes.append(f"Single project dominance: '{project_name}' - check for special event or data error")
            
            # Analyze branch concentration
            if top_branches and len(top_branches) <= 2:
                branch_names = ", ".join(top_branches.keys())
                causes.append(f"Limited branch participation: {branch_names} - investigate other branch activity")
            
            # Check for data quality issues
            z_score = abs(metrics.get('z_score', 0))
            if z_score > 4:
                causes.append("Extreme statistical deviation detected - verify data collection accuracy")
            
            # Analyze time-of-week patterns if available
            if hasattr(df, 'date') and not df.empty:
                df_copy = df.copy()
                df_copy['weekday'] = pd.to_datetime(df_copy['date']).dt.dayofweek
                weekend_ratio = (df_copy['weekday'] >= 5).mean()
                if weekend_ratio > 0.7:
                    causes.append("High weekend activity - special events or different volunteer schedules")
                elif weekend_ratio < 0.1:
                    causes.append("Weekday-only activity - check weekend program availability")
            
        except Exception as e:
            logger.error(f"Error in hours anomaly cause analysis: {e}")
        
        return causes
    
    def analyze_project_stall_causes(self, alert: AnomalyAlert) -> List[str]:
        """Analyze causes for project activity stalls"""
        causes = alert.root_cause_hints.copy()
        
        try:
            metrics = alert.metrics
            decline_ratio = metrics.get('decline_ratio', 0)
            project_id = metrics.get('project_id')
            
            # Severity-based analysis
            if decline_ratio > 0.9:
                causes.append("Near-complete activity cessation - project may be completed or cancelled")
            elif decline_ratio > 0.7:
                causes.append("Significant decline - check project leadership and volunteer coordination")
            
            # Analyze project lifecycle stage
            if project_id and not self.interactions_df.empty:
                project_data = self.interactions_df[self.interactions_df['project_id'] == project_id]
                if not project_data.empty:
                    project_duration = (pd.to_datetime(project_data['date'].max()) - 
                                      pd.to_datetime(project_data['date'].min())).days
                    
                    if project_duration > 365:
                        causes.append("Long-running project - may be experiencing volunteer fatigue")
                    elif project_duration < 30:
                        causes.append("New project with declining activity - check onboarding and expectations")
            
        except Exception as e:
            logger.error(f"Error in project stall cause analysis: {e}")
        
        return causes
    
    def _is_holiday_period(self, date: pd.Timestamp) -> bool:
        """Check if date falls in common holiday periods"""
        month = date.month
        day = date.day
        
        # Major holiday periods
        holiday_periods = [
            (11, 20, 12, 5),    # Thanksgiving to early December
            (12, 20, 1, 5),     # Christmas/New Year
            (5, 25, 6, 5),      # Memorial Day period
            (7, 1, 7, 10),      # July 4th period
            (8, 15, 9, 5),      # Late summer/back-to-school
        ]
        
        for start_month, start_day, end_month, end_day in holiday_periods:
            if (month == start_month and day >= start_day) or \
               (month == end_month and day <= end_day) or \
               (start_month < month < end_month):
                return True
        
        return False
    
    def _is_weather_sensitive_period(self, date: pd.Timestamp) -> bool:
        """Check if date falls in weather-sensitive periods"""
        month = date.month
        
        # Winter months and severe weather seasons
        return month in [12, 1, 2, 6, 7, 8]  # Winter and peak summer
    
    def _is_academic_transition_period(self, date: pd.Timestamp) -> bool:
        """Check if date falls during academic transitions"""
        month = date.month
        
        # Academic transition periods
        return month in [1, 5, 8, 9]  # Semester starts/ends
    
    def enhance_alert_with_analysis(self, alert: AnomalyAlert, df: pd.DataFrame) -> AnomalyAlert:
        """Enhance alert with detailed root cause analysis"""
        try:
            if alert.anomaly_type == AnomalyType.VOLUNTEER_DROP:
                alert.root_cause_hints = self.analyze_volunteer_drop_causes(alert, df)
            elif alert.anomaly_type in [AnomalyType.HOURS_SPIKE, AnomalyType.HOURS_DROP]:
                alert.root_cause_hints = self.analyze_hours_anomaly_causes(alert, df)
            elif alert.anomaly_type == AnomalyType.PROJECT_STALL:
                alert.root_cause_hints = self.analyze_project_stall_causes(alert)
            
            # Add general organizational factors
            alert.root_cause_hints.extend(self._get_organizational_factors())
            
            # Remove duplicates while preserving order
            seen = set()
            alert.root_cause_hints = [x for x in alert.root_cause_hints if not (x in seen or seen.add(x))]
            
        except Exception as e:
            logger.error(f"Error enhancing alert analysis: {e}")
        
        return alert
    
    def _get_organizational_factors(self) -> List[str]:
        """Get general organizational factors that could impact volunteer activity"""
        return [
            "Check recent organizational communications or policy changes",
            "Review staff availability and program leadership",
            "Assess facility conditions and accessibility",
            "Consider community events or competing activities"
        ]


class AlertConfiguration:
    """Configuration management for anomaly alerting"""
    
    def __init__(self):
        self.config = self._load_default_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default alerting configuration"""
        return {
            "detection": {
                "enabled": True,
                "check_interval_hours": 24,
                "lookback_days": 30,
                "min_data_points": 7,
                "sensitivity_threshold": 2.0
            },
            "notifications": {
                "slack": {
                    "enabled": bool(os.getenv('SLACK_WEBHOOK_URL')),
                    "channel": "#alerts",
                    "severity_filter": ["medium", "high", "critical"]
                },
                "email": {
                    "enabled": bool(os.getenv('SMTP_USERNAME')),
                    "recipients": os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(','),
                    "severity_filter": ["high", "critical"]
                }
            },
            "alert_types": {
                "volunteer_drop": {"enabled": True, "min_severity": "medium"},
                "hours_spike": {"enabled": True, "min_severity": "medium"}, 
                "hours_drop": {"enabled": True, "min_severity": "medium"},
                "project_stall": {"enabled": True, "min_severity": "high"},
                "branch_anomaly": {"enabled": True, "min_severity": "medium"},
                "category_shift": {"enabled": False, "min_severity": "low"},
                "new_volunteer_plateau": {"enabled": True, "min_severity": "high"}
            },
            "rate_limiting": {
                "max_alerts_per_hour": 10,
                "duplicate_suppression_hours": 24
            }
        }
    
    def should_send_notification(self, alert: AnomalyAlert, channel: str) -> bool:
        """Check if notification should be sent based on configuration"""
        try:
            # Check if alert type is enabled
            alert_config = self.config["alert_types"].get(alert.anomaly_type.value, {})
            if not alert_config.get("enabled", True):
                return False
            
            # Check severity threshold
            min_severity = alert_config.get("min_severity", "low")
            severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            
            if severity_order.get(alert.severity.value, 0) < severity_order.get(min_severity, 0):
                return False
            
            # Check notification channel configuration
            channel_config = self.config["notifications"].get(channel, {})
            if not channel_config.get("enabled", False):
                return False
            
            # Check severity filter for channel
            severity_filter = channel_config.get("severity_filter", [])
            if severity_filter and alert.severity.value not in severity_filter:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking notification configuration: {e}")
            return True  # Default to sending on error


class AnomalyAlertingOrchestrator:
    """Main orchestrator for the anomaly alerting system"""
    
    def __init__(self, volunteer_data: Dict[str, Any]):
        self.volunteer_data = volunteer_data
        self.detector = AnomalyDetector(volunteer_data)
        self.root_cause_analyzer = RootCauseAnalyzer(volunteer_data)
        self.slack_notifier = SlackNotifier()
        self.email_notifier = EmailNotifier()
        self.config = AlertConfiguration()
        self.alert_history: List[AnomalyAlert] = []
        
    async def run_detection_cycle(self) -> List[AnomalyAlert]:
        """Run a complete anomaly detection and alerting cycle"""
        logger.info("Starting anomaly detection cycle...")
        
        try:
            # Detect anomalies
            alerts = self.detector.detect_anomalies(
                lookback_days=self.config.config["detection"]["lookback_days"]
            )
            
            if not alerts:
                logger.info("No anomalies detected")
                return []
            
            logger.info(f"Detected {len(alerts)} anomalies")
            
            # Enhance alerts with root cause analysis
            enhanced_alerts = []
            df = self.detector._prepare_timeseries_data(
                self.config.config["detection"]["lookback_days"]
            )
            
            for alert in alerts:
                enhanced_alert = self.root_cause_analyzer.enhance_alert_with_analysis(alert, df)
                enhanced_alerts.append(enhanced_alert)
            
            # Filter and deduplicate alerts
            filtered_alerts = self._filter_alerts(enhanced_alerts)
            
            # Send notifications
            await self._send_notifications(filtered_alerts)
            
            # Store alert history
            self.alert_history.extend(filtered_alerts)
            
            # Keep only recent history (last 7 days)
            cutoff_time = datetime.now() - timedelta(days=7)
            self.alert_history = [a for a in self.alert_history if a.timestamp > cutoff_time]
            
            logger.info(f"Completed anomaly detection cycle with {len(filtered_alerts)} alerts")
            return filtered_alerts
            
        except Exception as e:
            logger.error(f"Error in detection cycle: {e}")
            return []
    
    def _filter_alerts(self, alerts: List[AnomalyAlert]) -> List[AnomalyAlert]:
        """Filter alerts based on configuration and deduplication"""
        filtered = []
        
        for alert in alerts:
            # Check if alert type is enabled
            if not self.config.config["alert_types"].get(alert.anomaly_type.value, {}).get("enabled", True):
                continue
            
            # Check for duplicates in recent history
            if self._is_duplicate_alert(alert):
                logger.info(f"Suppressing duplicate alert: {alert.title}")
                continue
            
            filtered.append(alert)
        
        # Respect rate limiting
        max_alerts = self.config.config["rate_limiting"]["max_alerts_per_hour"]
        if len(filtered) > max_alerts:
            # Keep highest severity alerts
            filtered.sort(key=lambda x: (x.severity.value, x.timestamp), reverse=True)
            filtered = filtered[:max_alerts]
            logger.warning(f"Rate limiting applied: showing top {max_alerts} alerts")
        
        return filtered
    
    def _is_duplicate_alert(self, alert: AnomalyAlert) -> bool:
        """Check if alert is a duplicate of recent alerts"""
        suppression_hours = self.config.config["rate_limiting"]["duplicate_suppression_hours"]
        cutoff_time = datetime.now() - timedelta(hours=suppression_hours)
        
        for historical_alert in self.alert_history:
            if historical_alert.timestamp < cutoff_time:
                continue
                
            if (historical_alert.anomaly_type == alert.anomaly_type and
                historical_alert.title == alert.title):
                return True
        
        return False
    
    async def _send_notifications(self, alerts: List[AnomalyAlert]) -> None:
        """Send notifications for alerts"""
        if not alerts:
            return
        
        # Send individual alerts
        for alert in alerts:
            # Slack notifications
            if self.config.should_send_notification(alert, "slack"):
                try:
                    channel = self.config.config["notifications"]["slack"]["channel"]
                    await self.slack_notifier.send_alert(alert, channel)
                except Exception as e:
                    logger.error(f"Error sending Slack alert: {e}")
            
            # Email notifications
            if self.config.should_send_notification(alert, "email"):
                try:
                    recipients = self.config.config["notifications"]["email"]["recipients"]
                    recipients = [r.strip() for r in recipients if r.strip()]
                    if recipients:
                        await self.email_notifier.send_alert(alert, recipients)
                except Exception as e:
                    logger.error(f"Error sending email alert: {e}")
        
        # Send summary report if multiple alerts
        if len(alerts) > 3:
            try:
                if self.config.config["notifications"]["slack"]["enabled"]:
                    channel = self.config.config["notifications"]["slack"]["channel"]
                    await self.slack_notifier.send_summary_report(alerts, channel)
            except Exception as e:
                logger.error(f"Error sending summary report: {e}")
    
    async def run_continuous_monitoring(self, interval_hours: int = 24) -> None:
        """Run continuous anomaly monitoring"""
        logger.info(f"Starting continuous monitoring with {interval_hours}h intervals")
        
        while True:
            try:
                await self.run_detection_cycle()
                await asyncio.sleep(interval_hours * 3600)  # Convert to seconds
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    def get_alert_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of recent alerts"""
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_alerts = [a for a in self.alert_history if a.timestamp > cutoff_time]
        
        if not recent_alerts:
            return {"total": 0, "by_severity": {}, "by_type": {}}
        
        severity_counts = {}
        type_counts = {}
        
        for alert in recent_alerts:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            type_counts[alert.anomaly_type.value] = type_counts.get(alert.anomaly_type.value, 0) + 1
        
        return {
            "total": len(recent_alerts),
            "by_severity": severity_counts,
            "by_type": type_counts,
            "latest_alert": recent_alerts[-1].timestamp.isoformat() if recent_alerts else None
        }