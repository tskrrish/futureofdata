"""
Renewal Alert System for E-Sign Vault
Handles automated renewal notifications and scheduling
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from jinja2 import Template

from database import VolunteerDatabase
from config import settings

logger = logging.getLogger(__name__)

class RenewalAlertService:
    def __init__(self):
        """Initialize the Renewal Alert Service"""
        self.database = VolunteerDatabase()
        self.email_config = {
            'smtp_server': getattr(settings, 'SMTP_SERVER', 'localhost'),
            'smtp_port': getattr(settings, 'SMTP_PORT', 587),
            'smtp_username': getattr(settings, 'SMTP_USERNAME', ''),
            'smtp_password': getattr(settings, 'SMTP_PASSWORD', ''),
            'from_email': getattr(settings, 'FROM_EMAIL', 'noreply@ymca.org')
        }
        
        # Email templates
        self.email_templates = {
            'renewal_reminder': Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Document Renewal Reminder - YMCA</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #1e40af; color: white; padding: 20px; text-align: center;">
        <h1>YMCA Document Renewal Reminder</h1>
    </div>
    
    <div style="padding: 20px; background-color: #f8fafc; border: 1px solid #e2e8f0;">
        <h2>Hello {{ user_name }},</h2>
        
        <p>This is a friendly reminder that your YMCA document is scheduled to expire soon.</p>
        
        <div style="background-color: white; padding: 15px; border-left: 4px solid #f59e0b; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #92400e;">Document Details</h3>
            <p><strong>Document:</strong> {{ document_name }}</p>
            <p><strong>Type:</strong> {{ document_type }}</p>
            <p><strong>Expires:</strong> {{ expiry_date }}</p>
            <p><strong>Days Until Expiry:</strong> {{ days_until_expiry }}</p>
        </div>
        
        {% if days_until_expiry <= 7 %}
        <div style="background-color: #fef2f2; padding: 15px; border-left: 4px solid #ef4444; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #dc2626;">Urgent Action Required</h3>
            <p>Your document expires in {{ days_until_expiry }} day(s). Please renew it immediately to avoid any interruption in your volunteer activities.</p>
        </div>
        {% endif %}
        
        <h3>Next Steps:</h3>
        <ul>
            <li>Contact your volunteer coordinator to begin the renewal process</li>
            <li>Prepare any required documentation</li>
            <li>Schedule necessary appointments (if applicable)</li>
            <li>Complete renewal requirements before the expiry date</li>
        </ul>
        
        <div style="background-color: #eff6ff; padding: 15px; border-left: 4px solid #3b82f6; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #1d4ed8;">Important Information</h3>
            <p>Document Type: <strong>{{ document_type }}</strong></p>
            {% if document_type == 'background_check' %}
            <p>Background checks typically take 7-10 business days to process. Please start your renewal process early.</p>
            {% elif document_type == 'certification' %}
            <p>Certifications may require training or testing. Please check with your coordinator for specific requirements.</p>
            {% elif document_type == 'waiver' %}
            <p>Liability waivers can usually be renewed online or in person at your YMCA branch.</p>
            {% endif %}
        </div>
        
        <p>If you have any questions or need assistance with the renewal process, please contact:</p>
        <ul>
            <li><strong>Email:</strong> volunteers@ymca.org</li>
            <li><strong>Phone:</strong> (513) 881-9622</li>
            <li><strong>Website:</strong> <a href="https://www.myy.org/volunteering">www.myy.org/volunteering</a></li>
        </ul>
        
        <p>Thank you for your continued commitment to volunteering with the YMCA!</p>
        
        <p style="margin-top: 30px;">
            Best regards,<br>
            <strong>YMCA Volunteer Team</strong><br>
            YMCA of Greater Cincinnati
        </p>
    </div>
    
    <div style="background-color: #374151; color: white; padding: 15px; text-align: center; font-size: 12px;">
        <p>This is an automated reminder from the YMCA E-Sign Vault system.</p>
        <p>Please do not reply to this email. For assistance, contact volunteers@ymca.org</p>
    </div>
</body>
</html>
            """),
            
            'renewal_summary': Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Document Renewal Summary - YMCA Admin</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #1e40af; color: white; padding: 20px; text-align: center;">
        <h1>Document Renewal Summary</h1>
        <p>{{ summary_date }}</p>
    </div>
    
    <div style="padding: 20px; background-color: #f8fafc;">
        <h2>Overview</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
            <div style="background-color: white; padding: 15px; text-align: center; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; color: #dc2626;">{{ urgent_count }}</h3>
                <p style="margin: 5px 0; color: #6b7280;">Urgent (≤7 days)</p>
            </div>
            <div style="background-color: white; padding: 15px; text-align: center; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; color: #f59e0b;">{{ warning_count }}</h3>
                <p style="margin: 5px 0; color: #6b7280;">Warning (8-14 days)</p>
            </div>
            <div style="background-color: white; padding: 15px; text-align: center; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; color: #3b82f6;">{{ notice_count }}</h3>
                <p style="margin: 5px 0; color: #6b7280;">Notice (15-30 days)</p>
            </div>
            <div style="background-color: white; padding: 15px; text-align: center; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; color: #059669;">{{ total_count }}</h3>
                <p style="margin: 5px 0; color: #6b7280;">Total Documents</p>
            </div>
        </div>
        
        {% for category, documents in documents_by_urgency.items() %}
        <div style="margin: 30px 0;">
            <h3>{{ category.replace('_', ' ').title() }}</h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white;">
                <thead>
                    <tr style="background-color: #f3f4f6;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #d1d5db;">User</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #d1d5db;">Document</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #d1d5db;">Type</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #d1d5db;">Expires</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #d1d5db;">Days Left</th>
                    </tr>
                </thead>
                <tbody>
                    {% for doc in documents %}
                    <tr>
                        <td style="padding: 10px; border: 1px solid #d1d5db;">{{ doc.user_name }}</td>
                        <td style="padding: 10px; border: 1px solid #d1d5db;">{{ doc.document_name }}</td>
                        <td style="padding: 10px; border: 1px solid #d1d5db;">{{ doc.document_type }}</td>
                        <td style="padding: 10px; border: 1px solid #d1d5db;">{{ doc.expiry_date }}</td>
                        <td style="padding: 10px; border: 1px solid #d1d5db;">
                            <span style="color: {% if doc.days_until_expiry <= 7 %}#dc2626{% elif doc.days_until_expiry <= 14 %}#f59e0b{% else %}#3b82f6{% endif %};">
                                {{ doc.days_until_expiry }}
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
    </div>
</body>
</html>
            """)
        }
    
    async def send_renewal_reminder(self, document: Dict[str, Any], user: Dict[str, Any]) -> bool:
        """Send a renewal reminder email to a user"""
        try:
            # Calculate days until expiry
            expiry_date = datetime.fromisoformat(document['expiry_date'].replace('Z', '+00:00'))
            days_until_expiry = (expiry_date - datetime.now()).days
            
            # Prepare template data
            template_data = {
                'user_name': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or 'Volunteer',
                'document_name': document.get('document_name', ''),
                'document_type': document.get('document_type', '').replace('_', ' ').title(),
                'expiry_date': expiry_date.strftime('%B %d, %Y'),
                'days_until_expiry': days_until_expiry
            }
            
            # Render email content
            html_content = self.email_templates['renewal_reminder'].render(**template_data)
            
            # Create email message
            msg = MimeMultipart('alternative')
            msg['Subject'] = f"YMCA Document Renewal Reminder - {document.get('document_type', '').replace('_', ' ').title()}"
            msg['From'] = self.email_config['from_email']
            msg['To'] = user.get('email', '')
            
            # Create plain text version
            text_content = f"""
Hello {template_data['user_name']},

This is a reminder that your YMCA document "{template_data['document_name']}" expires on {template_data['expiry_date']} ({days_until_expiry} days).

Please contact your volunteer coordinator to begin the renewal process.

Thank you,
YMCA Volunteer Team
            """.strip()
            
            # Attach both plain text and HTML versions
            text_part = MimeText(text_content, 'plain')
            html_part = MimeText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            await self._send_email(msg)
            
            logger.info(f"Renewal reminder sent to {user.get('email')} for document {document['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending renewal reminder: {e}")
            return False
    
    async def send_admin_summary(self, admin_email: str, expiring_documents: Dict[str, Any]) -> bool:
        """Send a summary of expiring documents to administrators"""
        try:
            # Categorize documents by urgency
            documents_by_urgency = {
                'urgent': [],
                'warning': [],
                'notice': []
            }
            
            for doc in expiring_documents.get('documents', []):
                days_until = doc.get('days_until_expiry', 0)
                if days_until <= 7:
                    documents_by_urgency['urgent'].append(doc)
                elif days_until <= 14:
                    documents_by_urgency['warning'].append(doc)
                else:
                    documents_by_urgency['notice'].append(doc)
            
            # Prepare template data
            template_data = {
                'summary_date': datetime.now().strftime('%B %d, %Y'),
                'urgent_count': len(documents_by_urgency['urgent']),
                'warning_count': len(documents_by_urgency['warning']),
                'notice_count': len(documents_by_urgency['notice']),
                'total_count': expiring_documents.get('total_expiring', 0),
                'documents_by_urgency': documents_by_urgency
            }
            
            # Render email content
            html_content = self.email_templates['renewal_summary'].render(**template_data)
            
            # Create email message
            msg = MimeMultipart('alternative')
            msg['Subject'] = f"YMCA Document Renewal Summary - {template_data['summary_date']}"
            msg['From'] = self.email_config['from_email']
            msg['To'] = admin_email
            
            # Create plain text version
            text_content = f"""
Document Renewal Summary - {template_data['summary_date']}

Urgent (≤7 days): {template_data['urgent_count']}
Warning (8-14 days): {template_data['warning_count']}
Notice (15-30 days): {template_data['notice_count']}
Total Documents: {template_data['total_count']}

Please review the detailed breakdown in your email client.
            """.strip()
            
            # Attach both versions
            text_part = MimeText(text_content, 'plain')
            html_part = MimeText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            await self._send_email(msg)
            
            logger.info(f"Admin summary sent to {admin_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending admin summary: {e}")
            return False
    
    async def _send_email(self, message: MimeMultipart) -> None:
        """Send email using SMTP"""
        try:
            # In development, just log the email instead of sending
            if not all([
                self.email_config['smtp_server'],
                self.email_config['smtp_username'],
                self.email_config['smtp_password']
            ]):
                logger.info(f"Email would be sent: {message['Subject']} to {message['To']}")
                return
            
            # Send actual email in production
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
                server.send_message(message)
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
    
    async def process_pending_alerts(self) -> Dict[str, int]:
        """Process all pending renewal alerts"""
        try:
            alerts = await self.database.get_pending_alerts()
            results = {'sent': 0, 'failed': 0}
            
            for alert in alerts:
                try:
                    # Get user information
                    user_info = alert.get('users', {})
                    document_info = alert.get('esign_documents', {})
                    
                    if not user_info.get('email'):
                        logger.warning(f"No email found for user in alert {alert['id']}")
                        results['failed'] += 1
                        continue
                    
                    # Send reminder email
                    success = await self.send_renewal_reminder(
                        {
                            'id': alert['document_id'],
                            'document_name': document_info.get('document_name', ''),
                            'document_type': document_info.get('document_type', ''),
                            'expiry_date': alert.get('alert_date', '')
                        },
                        user_info
                    )
                    
                    if success:
                        # Mark alert as sent
                        await self.database.mark_alert_sent(alert['id'])
                        results['sent'] += 1
                    else:
                        results['failed'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing alert {alert['id']}: {e}")
                    results['failed'] += 1
            
            logger.info(f"Processed alerts: {results['sent']} sent, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error processing pending alerts: {e}")
            return {'sent': 0, 'failed': 0}
    
    async def schedule_renewal_alerts_for_document(self, document_id: str, user_id: str, expiry_date: str) -> int:
        """Schedule renewal alerts for a specific document"""
        try:
            expiry_dt = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
            alert_days = [30, 14, 7]  # Days before expiry to send alerts
            scheduled_count = 0
            
            for days_before in alert_days:
                alert_date = expiry_dt - timedelta(days=days_before)
                
                # Only schedule if alert date is in the future
                if alert_date > datetime.now():
                    alert_data = {
                        'type': 'email',
                        'alert_date': alert_date.isoformat(),
                        'days_before': days_before,
                        'message': f'Your document expires in {days_before} days. Please renew it to maintain access.'
                    }
                    
                    success = await self.database.create_renewal_alert(document_id, user_id, alert_data)
                    if success:
                        scheduled_count += 1
            
            logger.info(f"Scheduled {scheduled_count} alerts for document {document_id}")
            return scheduled_count
            
        except Exception as e:
            logger.error(f"Error scheduling alerts for document {document_id}: {e}")
            return 0
    
    async def run_daily_alert_check(self) -> Dict[str, Any]:
        """Run daily check for expiring documents and send alerts"""
        try:
            logger.info("Starting daily alert check...")
            
            # Process pending alerts
            alert_results = await self.process_pending_alerts()
            
            # Get summary of expiring documents
            from esign_vault import ESignVaultService
            vault_service = ESignVaultService()
            expiring_summary = await vault_service.get_expiring_documents_summary(30)
            
            # Send admin summary if there are expiring documents
            admin_email = getattr(settings, 'ADMIN_EMAIL', None)
            admin_summary_sent = False
            
            if admin_email and expiring_summary['total_expiring'] > 0:
                admin_summary_sent = await self.send_admin_summary(admin_email, expiring_summary)
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'alerts_processed': alert_results,
                'expiring_documents': expiring_summary,
                'admin_summary_sent': admin_summary_sent
            }
            
            logger.info(f"Daily alert check completed: {alert_results['sent']} alerts sent")
            return results
            
        except Exception as e:
            logger.error(f"Error in daily alert check: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'alerts_processed': {'sent': 0, 'failed': 0},
                'expiring_documents': {'total_expiring': 0},
                'admin_summary_sent': False
            }


# Background task runner
async def run_renewal_alert_service():
    """Background task to run renewal alert checks"""
    alert_service = RenewalAlertService()
    
    while True:
        try:
            # Run daily check
            results = await alert_service.run_daily_alert_check()
            logger.info(f"Alert service run completed: {results}")
            
            # Wait 24 hours before next check
            await asyncio.sleep(24 * 60 * 60)  # 24 hours
            
        except Exception as e:
            logger.error(f"Error in renewal alert service: {e}")
            # Wait 1 hour before retrying on error
            await asyncio.sleep(60 * 60)  # 1 hour


if __name__ == "__main__":
    # Test the renewal alert service
    async def test_alerts():
        service = RenewalAlertService()
        results = await service.run_daily_alert_check()
        print("Alert check results:", results)
    
    asyncio.run(test_alerts())