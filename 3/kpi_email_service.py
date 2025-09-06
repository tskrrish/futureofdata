"""
KPI Email Reporting Service for YMCA Volunteer System
Automated reporting system that sends KPI snapshots to stakeholders
"""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import pandas as pd
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from jinja2 import Template

from database import VolunteerDatabase
from data_processor import VolunteerDataProcessor
from config import settings

logger = logging.getLogger(__name__)

@dataclass
class KPISnapshot:
    """Data structure for KPI snapshot"""
    report_date: str
    period: str
    total_hours: float
    active_volunteers: int
    member_volunteers: int
    total_projects: int
    avg_hours_per_volunteer: float
    member_engagement_rate: float
    top_branch: str
    top_category: str
    yde_impact_pct: float
    monthly_trends: List[Dict]
    branch_performance: List[Dict]
    project_category_stats: List[Dict]
    insights: List[Dict]
    generated_at: str

@dataclass 
class StakeholderConfig:
    """Configuration for email stakeholders"""
    email: str
    name: str
    role: str
    report_frequency: str  # daily, weekly, monthly
    branches: List[str]  # specific branches or ["all"]
    active: bool = True

class KPIEmailService:
    """Service for generating and sending automated KPI email reports"""
    
    def __init__(self, database: VolunteerDatabase, data_processor: VolunteerDataProcessor = None):
        self.database = database
        self.data_processor = data_processor
        self.stakeholders: List[StakeholderConfig] = []
        self.email_template = None
        self._load_stakeholders()
        self._load_email_template()
    
    def _load_stakeholders(self):
        """Load stakeholder configuration from database or config file"""
        try:
            # Try to load from database first
            # Fallback to default configuration
            default_stakeholders = [
                {
                    "email": "director@ymcacincinnati.org",
                    "name": "Executive Director",
                    "role": "Executive",
                    "report_frequency": "weekly",
                    "branches": ["all"],
                    "active": True
                },
                {
                    "email": "volunteer.coordinator@ymcacincinnati.org", 
                    "name": "Volunteer Coordinator",
                    "role": "Operations",
                    "report_frequency": "daily",
                    "branches": ["all"],
                    "active": True
                },
                {
                    "email": "branch.manager1@ymcacincinnati.org",
                    "name": "Branch Manager - Blue Ash",
                    "role": "Branch Management", 
                    "report_frequency": "weekly",
                    "branches": ["Blue Ash YMCA"],
                    "active": True
                },
                {
                    "email": "branch.manager2@ymcacincinnati.org",
                    "name": "Branch Manager - M.E. Lyons",
                    "role": "Branch Management",
                    "report_frequency": "weekly", 
                    "branches": ["M.E. Lyons YMCA"],
                    "active": True
                }
            ]
            
            self.stakeholders = [StakeholderConfig(**config) for config in default_stakeholders]
            logger.info(f"Loaded {len(self.stakeholders)} stakeholder configurations")
            
        except Exception as e:
            logger.error(f"Error loading stakeholders: {e}")
            self.stakeholders = []
    
    def _load_email_template(self):
        """Load HTML email template"""
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YMCA Volunteer KPI Report</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: #c41e3a; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }
        .header h1 { margin: 0; font-size: 24px; }
        .period { background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 15px 0; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #c41e3a; }
        .metric-value { font-size: 24px; font-weight: bold; color: #c41e3a; }
        .metric-label { font-size: 12px; color: #666; text-transform: uppercase; }
        .section { margin: 25px 0; }
        .section h2 { color: #c41e3a; border-bottom: 2px solid #c41e3a; padding-bottom: 5px; }
        .insight { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #2196f3; }
        .insight.success { background: #e8f5e8; border-left-color: #4caf50; }
        .insight.warning { background: #fff3e0; border-left-color: #ff9800; }
        .table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background: #f5f5f5; font-weight: bold; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>YMCA Volunteer KPI Report</h1>
            <p>Generated on {{ kpi.generated_at }} | Period: {{ kpi.period }}</p>
        </div>
        
        <div class="period">
            <strong>Reporting Period:</strong> {{ kpi.period }} (as of {{ kpi.report_date }})
        </div>
        
        <div class="section">
            <h2>Key Performance Indicators</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{{ "{:,.1f}".format(kpi.total_hours) }}</div>
                    <div class="metric-label">Total Volunteer Hours</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ kpi.active_volunteers }}</div>
                    <div class="metric-label">Active Volunteers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ kpi.member_volunteers }}</div>
                    <div class="metric-label">YMCA Member Volunteers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ kpi.total_projects }}</div>
                    <div class="metric-label">Active Projects</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ "{:.1f}".format(kpi.avg_hours_per_volunteer) }}</div>
                    <div class="metric-label">Avg Hours per Volunteer</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ "{:.1f}%".format(kpi.member_engagement_rate) }}</div>
                    <div class="metric-label">Member Engagement Rate</div>
                </div>
            </div>
        </div>
        
        {% if kpi.insights %}
        <div class="section">
            <h2>Key Insights</h2>
            {% for insight in kpi.insights %}
            <div class="insight {{ insight.type }}">
                <strong>{{ insight.title }}:</strong> {{ insight.message }}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if kpi.branch_performance %}
        <div class="section">
            <h2>Top Performing Branches</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Branch</th>
                        <th>Total Hours</th>
                        <th>Active Volunteers</th>
                    </tr>
                </thead>
                <tbody>
                    {% for branch in kpi.branch_performance[:5] %}
                    <tr>
                        <td>{{ branch.branch }}</td>
                        <td>{{ "{:,.1f}".format(branch.hours) }}</td>
                        <td>{{ branch.get('active', '-') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if kpi.project_category_stats %}
        <div class="section">
            <h2>Project Category Performance</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Hours</th>
                        <th>Volunteers</th>
                        <th>Projects</th>
                    </tr>
                </thead>
                <tbody>
                    {% for category in kpi.project_category_stats[:5] %}
                    <tr>
                        <td>{{ category.project_tag }}</td>
                        <td>{{ "{:,.1f}".format(category.hours) }}</td>
                        <td>{{ category.volunteers }}</td>
                        <td>{{ category.projects }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <div class="section">
            <h2>Summary</h2>
            <p><strong>Top Branch:</strong> {{ kpi.top_branch }}</p>
            <p><strong>Top Category:</strong> {{ kpi.top_category }}</p>
            <p><strong>Youth Development Impact:</strong> {{ "{:.1f}%".format(kpi.yde_impact_pct) }} of total hours</p>
        </div>
        
        <div class="footer">
            <p>This report was automatically generated by the YMCA Volunteer PathFinder system.</p>
            <p>For questions or to modify your report preferences, contact your system administrator.</p>
        </div>
    </div>
</body>
</html>
        """
        
        self.email_template = Template(template_content)
        logger.info("Email template loaded successfully")
    
    async def generate_kpi_snapshot(self, period: str = "current_month", branch_filter: str = "All") -> KPISnapshot:
        """Generate KPI snapshot for specified period"""
        try:
            # Calculate date range based on period
            end_date = datetime.now()
            if period == "current_month":
                start_date = end_date.replace(day=1)
                period_display = f"{end_date.strftime('%B %Y')}"
            elif period == "last_month":
                first_day_current = end_date.replace(day=1)
                end_date = first_day_current - timedelta(days=1)
                start_date = end_date.replace(day=1)
                period_display = f"{end_date.strftime('%B %Y')}"
            elif period == "current_week":
                days_since_monday = end_date.weekday()
                start_date = end_date - timedelta(days=days_since_monday)
                period_display = f"Week of {start_date.strftime('%B %d, %Y')}"
            elif period == "last_week":
                days_since_monday = end_date.weekday()
                start_date = end_date - timedelta(days=days_since_monday + 7)
                end_date = start_date + timedelta(days=6)
                period_display = f"Week of {start_date.strftime('%B %d, %Y')}"
            else:
                # Default to current month
                start_date = end_date.replace(day=1)
                period_display = f"{end_date.strftime('%B %Y')}"
            
            # Load and process volunteer data
            if not self.data_processor:
                # Initialize with default data path
                self.data_processor = VolunteerDataProcessor(settings.VOLUNTEER_DATA_PATH)
            
            volunteer_data = self.data_processor.get_volunteer_recommendations_data()
            
            # Filter data by date range (simplified - would need actual date filtering)
            interactions_df = volunteer_data.get('interactions', pd.DataFrame())
            
            if interactions_df.empty:
                logger.warning("No interaction data available for KPI generation")
                return self._create_empty_snapshot(period_display)
            
            # Apply branch filter if specified
            if branch_filter != "All" and "branch" in interactions_df.columns:
                interactions_df = interactions_df[interactions_df['branch'] == branch_filter]
            
            # Calculate KPIs using similar logic to useVolunteerData.js
            total_hours = float(interactions_df.get('hours', pd.Series([0])).fillna(0).sum())
            
            # Active volunteers (deduplicated by assignee)
            active_volunteers = 0
            if 'assignee' in interactions_df.columns:
                active_volunteers = interactions_df['assignee'].dropna().nunique()
            
            # Member volunteers
            member_volunteers = 0
            if 'is_member' in interactions_df.columns:
                member_volunteers = interactions_df[interactions_df['is_member'] == True]['assignee'].dropna().nunique()
            
            # Total projects
            total_projects = 0
            if 'project_id' in interactions_df.columns:
                total_projects = interactions_df['project_id'].dropna().nunique()
            
            # Calculate derived metrics
            avg_hours_per_volunteer = total_hours / active_volunteers if active_volunteers > 0 else 0
            member_engagement_rate = (member_volunteers / active_volunteers * 100) if active_volunteers > 0 else 0
            
            # Branch performance
            branch_performance = []
            if 'branch' in interactions_df.columns:
                branch_hours = interactions_df.groupby('branch')['hours'].sum().fillna(0).sort_values(ascending=False)
                branch_volunteers = interactions_df.groupby('branch')['assignee'].nunique()
                
                for branch, hours in branch_hours.head(10).items():
                    branch_performance.append({
                        'branch': str(branch),
                        'hours': float(hours),
                        'active': int(branch_volunteers.get(branch, 0))
                    })
            
            # Project category stats
            project_category_stats = []
            if 'project_category' in interactions_df.columns:
                cat_hours = interactions_df.groupby('project_category')['hours'].sum().fillna(0).sort_values(ascending=False)
                cat_volunteers = interactions_df.groupby('project_category')['assignee'].nunique()
                cat_projects = interactions_df.groupby('project_category')['project_id'].nunique()
                
                for category, hours in cat_hours.head(10).items():
                    project_category_stats.append({
                        'project_tag': str(category),
                        'hours': float(hours),
                        'volunteers': int(cat_volunteers.get(category, 0)),
                        'projects': int(cat_projects.get(category, 0))
                    })
            
            # Top performers
            top_branch = branch_performance[0]['branch'] if branch_performance else "N/A"
            top_category = project_category_stats[0]['project_tag'] if project_category_stats else "N/A"
            
            # YDE impact calculation
            yde_hours = 0
            if project_category_stats:
                for cat in project_category_stats:
                    if 'yde' in cat['project_tag'].lower():
                        yde_hours += cat['hours']
            yde_impact_pct = (yde_hours / total_hours * 100) if total_hours > 0 else 0
            
            # Generate insights
            insights = self._generate_insights(
                total_hours, active_volunteers, member_volunteers, member_engagement_rate,
                branch_performance, project_category_stats, yde_impact_pct
            )
            
            # Monthly trends (simplified)
            monthly_trends = []
            if 'date' in interactions_df.columns:
                monthly_data = interactions_df.groupby(interactions_df['date'].dt.to_period('M')).agg({
                    'hours': 'sum',
                    'assignee': 'nunique'
                }).fillna(0)
                
                for period, data in monthly_data.tail(6).iterrows():
                    monthly_trends.append({
                        'month': str(period),
                        'hours': float(data['hours']),
                        'active': int(data['assignee'])
                    })
            
            return KPISnapshot(
                report_date=end_date.strftime('%Y-%m-%d'),
                period=period_display,
                total_hours=total_hours,
                active_volunteers=active_volunteers,
                member_volunteers=member_volunteers,
                total_projects=total_projects,
                avg_hours_per_volunteer=avg_hours_per_volunteer,
                member_engagement_rate=member_engagement_rate,
                top_branch=top_branch,
                top_category=top_category,
                yde_impact_pct=yde_impact_pct,
                monthly_trends=monthly_trends,
                branch_performance=branch_performance,
                project_category_stats=project_category_stats,
                insights=insights,
                generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            logger.error(f"Error generating KPI snapshot: {e}")
            return self._create_empty_snapshot(period_display if 'period_display' in locals() else "Unknown Period")
    
    def _create_empty_snapshot(self, period: str) -> KPISnapshot:
        """Create empty KPI snapshot when data is unavailable"""
        return KPISnapshot(
            report_date=datetime.now().strftime('%Y-%m-%d'),
            period=period,
            total_hours=0.0,
            active_volunteers=0,
            member_volunteers=0,
            total_projects=0,
            avg_hours_per_volunteer=0.0,
            member_engagement_rate=0.0,
            top_branch="N/A",
            top_category="N/A", 
            yde_impact_pct=0.0,
            monthly_trends=[],
            branch_performance=[],
            project_category_stats=[],
            insights=[{"type": "warning", "title": "Data Unavailable", "message": "Unable to generate KPI data at this time"}],
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def _generate_insights(self, total_hours: float, active_volunteers: int, member_volunteers: int,
                          member_engagement_rate: float, branch_performance: List[Dict], 
                          project_category_stats: List[Dict], yde_impact_pct: float) -> List[Dict]:
        """Generate actionable insights from KPI data"""
        insights = []
        
        # Top performing branch insight
        if branch_performance:
            top_branch = branch_performance[0]
            insights.append({
                "type": "success",
                "title": "Top Performing Branch",
                "message": f"{top_branch['branch']} leads with {top_branch['hours']:.1f} volunteer hours"
            })
        
        # Member engagement insight
        if member_engagement_rate > 60:
            insights.append({
                "type": "success",
                "title": "Strong Member Engagement",
                "message": f"{member_engagement_rate:.1f}% of volunteers are YMCA members"
            })
        elif member_engagement_rate < 30:
            insights.append({
                "type": "warning", 
                "title": "Low Member Engagement",
                "message": f"Only {member_engagement_rate:.1f}% of volunteers are members. Consider member recruitment strategies."
            })
        
        # YDE impact insight
        if yde_impact_pct > 30:
            insights.append({
                "type": "info",
                "title": "Strong YDE Impact", 
                "message": f"Youth Development & Education programs account for {yde_impact_pct:.1f}% of volunteer hours"
            })
        
        # High-impact volunteers
        avg_hours = total_hours / active_volunteers if active_volunteers > 0 else 0
        if avg_hours > 25:
            insights.append({
                "type": "success",
                "title": "Highly Engaged Volunteers",
                "message": f"Average volunteer contributes {avg_hours:.1f} hours, showing strong commitment"
            })
        
        return insights
    
    async def send_kpi_report(self, stakeholder: StakeholderConfig, kpi_snapshot: KPISnapshot) -> bool:
        """Send KPI report email to a specific stakeholder"""
        try:
            # Filter KPI data by stakeholder's branch preference
            filtered_kpi = self._filter_kpi_for_stakeholder(kpi_snapshot, stakeholder)
            
            # Generate email content
            html_content = self.email_template.render(kpi=filtered_kpi)
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"YMCA Volunteer KPI Report - {filtered_kpi.period}"
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = stakeholder.email
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            success = await self._send_email(msg)
            
            if success:
                # Log successful send
                await self.database.track_event(
                    "kpi_email_sent",
                    {
                        "stakeholder_email": stakeholder.email,
                        "stakeholder_role": stakeholder.role,
                        "report_period": filtered_kpi.period,
                        "total_hours": filtered_kpi.total_hours,
                        "active_volunteers": filtered_kpi.active_volunteers
                    }
                )
                logger.info(f"KPI report sent successfully to {stakeholder.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending KPI report to {stakeholder.email}: {e}")
            return False
    
    def _filter_kpi_for_stakeholder(self, kpi_snapshot: KPISnapshot, stakeholder: StakeholderConfig) -> KPISnapshot:
        """Filter KPI data based on stakeholder's branch preferences"""
        if "all" in stakeholder.branches:
            return kpi_snapshot
            
        # Create filtered copy for branch-specific stakeholders
        filtered_kpi = KPISnapshot(**asdict(kpi_snapshot))
        
        # Filter branch performance data
        filtered_kpi.branch_performance = [
            branch for branch in kpi_snapshot.branch_performance 
            if branch['branch'] in stakeholder.branches
        ]
        
        # Recalculate top branch for filtered data
        if filtered_kpi.branch_performance:
            filtered_kpi.top_branch = filtered_kpi.branch_performance[0]['branch']
        
        return filtered_kpi
    
    async def _send_email(self, msg: MIMEMultipart) -> bool:
        """Send email using SMTP configuration"""
        try:
            # Use environment variables for SMTP configuration
            smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = getattr(settings, 'SMTP_PORT', 587)
            smtp_username = getattr(settings, 'SMTP_USERNAME', '')
            smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
            
            if not smtp_username or not smtp_password:
                logger.warning("SMTP credentials not configured - email not sent")
                return False
            
            # Create SMTP session
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'], text)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False
    
    async def send_scheduled_reports(self, frequency: str) -> Dict[str, Any]:
        """Send reports to all stakeholders with matching frequency"""
        results = {
            "sent": 0,
            "failed": 0,
            "stakeholders": [],
            "errors": []
        }
        
        try:
            # Filter stakeholders by frequency
            target_stakeholders = [
                s for s in self.stakeholders 
                if s.active and s.report_frequency == frequency
            ]
            
            if not target_stakeholders:
                logger.info(f"No active stakeholders found for {frequency} reports")
                return results
            
            # Generate KPI snapshot
            period = self._get_period_for_frequency(frequency)
            kpi_snapshot = await self.generate_kpi_snapshot(period)
            
            # Send reports to each stakeholder
            for stakeholder in target_stakeholders:
                success = await self.send_kpi_report(stakeholder, kpi_snapshot)
                
                stakeholder_result = {
                    "email": stakeholder.email,
                    "name": stakeholder.name,
                    "role": stakeholder.role,
                    "success": success
                }
                
                results["stakeholders"].append(stakeholder_result)
                
                if success:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to send to {stakeholder.email}")
            
            logger.info(f"Completed {frequency} report sending: {results['sent']} sent, {results['failed']} failed")
            
        except Exception as e:
            logger.error(f"Error in scheduled report sending: {e}")
            results["errors"].append(str(e))
        
        return results
    
    def _get_period_for_frequency(self, frequency: str) -> str:
        """Map report frequency to appropriate period"""
        frequency_mapping = {
            "daily": "current_week",
            "weekly": "current_week", 
            "monthly": "current_month"
        }
        return frequency_mapping.get(frequency, "current_month")
    
    async def add_stakeholder(self, stakeholder_config: Dict[str, Any]) -> bool:
        """Add new stakeholder configuration"""
        try:
            stakeholder = StakeholderConfig(**stakeholder_config)
            self.stakeholders.append(stakeholder)
            
            # Save to database (implementation would depend on database schema)
            await self.database.track_event(
                "stakeholder_added",
                {"stakeholder": asdict(stakeholder)}
            )
            
            logger.info(f"Added new stakeholder: {stakeholder.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding stakeholder: {e}")
            return False
    
    async def update_stakeholder(self, email: str, updates: Dict[str, Any]) -> bool:
        """Update existing stakeholder configuration"""
        try:
            for i, stakeholder in enumerate(self.stakeholders):
                if stakeholder.email == email:
                    # Update stakeholder
                    updated_data = asdict(stakeholder)
                    updated_data.update(updates)
                    self.stakeholders[i] = StakeholderConfig(**updated_data)
                    
                    logger.info(f"Updated stakeholder: {email}")
                    return True
            
            logger.warning(f"Stakeholder not found: {email}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating stakeholder: {e}")
            return False
    
    def get_stakeholders(self) -> List[Dict[str, Any]]:
        """Get all stakeholder configurations"""
        return [asdict(stakeholder) for stakeholder in self.stakeholders]