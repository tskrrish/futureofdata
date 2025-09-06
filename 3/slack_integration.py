"""
Slack Integration for YMCA Volunteer Shift Notifications and Approvals
Handles channel announcements, DMs, and approval workflows
"""
import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from pydantic import BaseModel

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShiftNotification(BaseModel):
    shift_id: str
    volunteer_id: str
    volunteer_name: str
    volunteer_email: str
    shift_title: str
    shift_description: str
    start_time: datetime
    end_time: datetime
    location: str
    branch: str
    coordinator_email: Optional[str] = None
    skills_required: Optional[List[str]] = None
    notification_type: str = "new"  # new, reminder, cancellation, update

class ApprovalRequest(BaseModel):
    request_id: str
    volunteer_id: str
    volunteer_name: str
    volunteer_email: str
    shift_id: str
    shift_title: str
    request_type: str  # signup, cancellation, schedule_change
    request_details: Dict[str, Any]
    approver_email: str
    created_at: datetime

class SlackConfig:
    def __init__(self):
        self.bot_token = os.getenv('SLACK_BOT_TOKEN', '')
        self.app_token = os.getenv('SLACK_APP_TOKEN', '')
        self.signing_secret = os.getenv('SLACK_SIGNING_SECRET', '')
        
        # Channel configurations
        self.general_announcements_channel = os.getenv('SLACK_ANNOUNCEMENTS_CHANNEL', '#volunteer-announcements')
        self.shift_notifications_channel = os.getenv('SLACK_SHIFT_CHANNEL', '#shift-notifications')
        self.approvals_channel = os.getenv('SLACK_APPROVALS_CHANNEL', '#volunteer-approvals')
        
        if not all([self.bot_token, self.signing_secret]):
            logger.warning("Slack configuration incomplete. Some features may not work.")

class SlackIntegration:
    def __init__(self):
        self.config = SlackConfig()
        
        # Initialize Slack clients
        try:
            self.client = WebClient(token=self.config.bot_token)
            
            # Initialize Slack Bolt app for interactive features
            self.app = App(
                token=self.config.bot_token,
                signing_secret=self.config.signing_secret,
                process_before_response=True
            )
            
            # Set up event handlers
            self._setup_event_handlers()
            
            logger.info("Slack integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Slack integration: {e}")
            self.client = None
            self.app = None

    def _setup_event_handlers(self):
        """Set up Slack event handlers for interactive components"""
        if not self.app:
            return

        @self.app.action("approve_shift_signup")
        def handle_approve_signup(ack, body, client):
            ack()
            self._handle_approval_action(body, "approved", client)

        @self.app.action("deny_shift_signup")
        def handle_deny_signup(ack, body, client):
            ack()
            self._handle_approval_action(body, "denied", client)

        @self.app.command("/shift-status")
        def handle_shift_status_command(ack, respond, command):
            ack()
            # Get shift status for volunteer
            volunteer_info = self._get_volunteer_shifts(command['user_id'])
            respond(volunteer_info)

    def _handle_approval_action(self, body: Dict, action: str, client):
        """Handle approval/denial actions from Slack buttons"""
        try:
            # Extract request details from button value
            request_data = json.loads(body['actions'][0]['value'])
            request_id = request_data['request_id']
            volunteer_id = request_data['volunteer_id']
            shift_id = request_data['shift_id']
            
            # Update approval status (this would integrate with your database)
            self._update_approval_status(request_id, action, body['user']['id'])
            
            # Send confirmation to approver
            client.chat_postMessage(
                channel=body['user']['id'],
                text=f"✅ Request {request_id} has been {action}."
            )
            
            # Notify volunteer of decision
            volunteer_slack_id = self._get_volunteer_slack_id(volunteer_id)
            if volunteer_slack_id:
                message = f"Your shift request has been {action}."
                if action == "approved":
                    message += " You're all set for your volunteer shift!"
                else:
                    message += " Please contact your coordinator if you have questions."
                
                client.chat_postMessage(
                    channel=volunteer_slack_id,
                    text=message
                )
                
        except Exception as e:
            logger.error(f"Error handling approval action: {e}")

    async def send_channel_announcement(self, notification: ShiftNotification) -> bool:
        """Send shift announcement to general channel"""
        if not self.client:
            logger.error("Slack client not initialized")
            return False

        try:
            # Create announcement message
            blocks = self._create_shift_announcement_blocks(notification)
            
            result = self.client.chat_postMessage(
                channel=self.config.general_announcements_channel,
                blocks=blocks,
                text=f"New volunteer shift available: {notification.shift_title}"
            )
            
            logger.info(f"Sent channel announcement for shift {notification.shift_id}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Error sending channel announcement: {e.response['error']}")
            return False

    async def send_direct_message(self, notification: ShiftNotification) -> bool:
        """Send direct message to volunteer about their shift"""
        if not self.client:
            logger.error("Slack client not initialized")
            return False

        try:
            # Get volunteer's Slack user ID
            volunteer_slack_id = self._get_volunteer_slack_id(notification.volunteer_id)
            if not volunteer_slack_id:
                logger.warning(f"No Slack ID found for volunteer {notification.volunteer_id}")
                return False

            # Create DM message
            blocks = self._create_shift_dm_blocks(notification)
            
            result = self.client.chat_postMessage(
                channel=volunteer_slack_id,
                blocks=blocks,
                text=f"Shift notification: {notification.shift_title}"
            )
            
            logger.info(f"Sent DM to volunteer {notification.volunteer_id} for shift {notification.shift_id}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Error sending DM: {e.response['error']}")
            return False

    async def send_approval_request(self, approval: ApprovalRequest) -> bool:
        """Send approval request to designated approvers"""
        if not self.client:
            logger.error("Slack client not initialized")
            return False

        try:
            # Get approver's Slack user ID
            approver_slack_id = self._get_approver_slack_id(approval.approver_email)
            if not approver_slack_id:
                logger.warning(f"No Slack ID found for approver {approval.approver_email}")
                return False

            # Create approval request message with interactive buttons
            blocks = self._create_approval_request_blocks(approval)
            
            result = self.client.chat_postMessage(
                channel=approver_slack_id,
                blocks=blocks,
                text=f"Approval needed: {approval.volunteer_name} - {approval.shift_title}"
            )
            
            logger.info(f"Sent approval request {approval.request_id} to {approval.approver_email}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Error sending approval request: {e.response['error']}")
            return False

    async def send_shift_reminder(self, notification: ShiftNotification, hours_before: int = 24) -> bool:
        """Send reminder about upcoming shift"""
        notification.notification_type = "reminder"
        
        # Send both channel announcement and DM
        channel_sent = await self.send_channel_announcement(notification)
        dm_sent = await self.send_direct_message(notification)
        
        return channel_sent or dm_sent

    def _create_shift_announcement_blocks(self, notification: ShiftNotification) -> List[Dict]:
        """Create Slack blocks for shift announcements"""
        formatted_start = notification.start_time.strftime("%A, %B %d at %I:%M %p")
        duration_hours = (notification.end_time - notification.start_time).total_seconds() / 3600
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🌟 {notification.shift_title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*When:* {formatted_start}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Duration:* {duration_hours:.1f} hours"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Location:* {notification.location}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Branch:* {notification.branch}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:* {notification.shift_description}"
                }
            }
        ]
        
        if notification.skills_required:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Skills Needed:* {', '.join(notification.skills_required)}"
                }
            })
        
        # Add call-to-action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Sign Up",
                        "emoji": True
                    },
                    "style": "primary",
                    "url": f"https://cincinnatiymca.volunteermatters.org/project/{notification.shift_id}",
                    "action_id": "signup_shift"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Learn More",
                        "emoji": True
                    },
                    "url": settings.YMCA_VOLUNTEER_PAGE,
                    "action_id": "learn_more"
                }
            ]
        })
        
        return blocks

    def _create_shift_dm_blocks(self, notification: ShiftNotification) -> List[Dict]:
        """Create Slack blocks for direct messages about shifts"""
        emoji_map = {
            "new": "🆕",
            "reminder": "⏰",
            "cancellation": "❌",
            "update": "📝"
        }
        
        emoji = emoji_map.get(notification.notification_type, "📋")
        
        if notification.notification_type == "reminder":
            title = f"{emoji} Shift Reminder: {notification.shift_title}"
            time_text = f"Your shift starts {notification.start_time.strftime('%A, %B %d at %I:%M %p')}"
        elif notification.notification_type == "cancellation":
            title = f"{emoji} Shift Cancelled: {notification.shift_title}"
            time_text = f"The shift scheduled for {notification.start_time.strftime('%A, %B %d at %I:%M %p')} has been cancelled."
        else:
            title = f"{emoji} Shift Confirmation: {notification.shift_title}"
            time_text = f"You're signed up for {notification.start_time.strftime('%A, %B %d at %I:%M %p')}"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hi {notification.volunteer_name}! 👋\n\n{time_text}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Location:* {notification.location}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Branch:* {notification.branch}"
                    }
                ]
            }
        ]
        
        if notification.notification_type != "cancellation":
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*What you'll be doing:* {notification.shift_description}"
                }
            })
            
            if notification.coordinator_email:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Questions?* Contact your coordinator at {notification.coordinator_email}"
                    }
                })
        
        return blocks

    def _create_approval_request_blocks(self, approval: ApprovalRequest) -> List[Dict]:
        """Create Slack blocks for approval requests"""
        request_details_text = json.dumps(approval.request_details, indent=2) if approval.request_details else "No additional details"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔔 Approval Required: {approval.request_type.title()}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Volunteer:* {approval.volunteer_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Email:* {approval.volunteer_email}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Shift:* {approval.shift_title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Request Type:* {approval.request_type}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Details:*\n```{request_details_text}```"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Approve",
                            "emoji": True
                        },
                        "style": "primary",
                        "action_id": "approve_shift_signup",
                        "value": json.dumps({
                            "request_id": approval.request_id,
                            "volunteer_id": approval.volunteer_id,
                            "shift_id": approval.shift_id
                        })
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Deny",
                            "emoji": True
                        },
                        "style": "danger",
                        "action_id": "deny_shift_signup",
                        "value": json.dumps({
                            "request_id": approval.request_id,
                            "volunteer_id": approval.volunteer_id,
                            "shift_id": approval.shift_id
                        })
                    }
                ]
            }
        ]
        
        return blocks

    def _get_volunteer_slack_id(self, volunteer_id: str) -> Optional[str]:
        """Get Slack user ID for volunteer (placeholder - implement based on your user system)"""
        # This would integrate with your user database to map volunteer IDs to Slack user IDs
        # For now, returning None as placeholder
        return None

    def _get_approver_slack_id(self, approver_email: str) -> Optional[str]:
        """Get Slack user ID for approver by email"""
        if not self.client:
            return None
            
        try:
            result = self.client.users_lookupByEmail(email=approver_email)
            return result['user']['id']
        except SlackApiError as e:
            logger.warning(f"Could not find Slack user for email {approver_email}: {e}")
            return None

    def _update_approval_status(self, request_id: str, status: str, approver_slack_id: str):
        """Update approval status in database (placeholder)"""
        # This would update your database with the approval status
        logger.info(f"Approval {request_id} {status} by {approver_slack_id}")

    def _get_volunteer_shifts(self, slack_user_id: str) -> str:
        """Get volunteer's upcoming shifts (placeholder)"""
        # This would query your database for the volunteer's shifts
        return "Your upcoming shifts:\n• No shifts scheduled"

    def get_request_handler(self):
        """Get the Slack request handler for FastAPI integration"""
        if not self.app:
            return None
        return SlackRequestHandler(self.app)

# Singleton instance
slack_integration = SlackIntegration()