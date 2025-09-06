"""
Example usage of the YMCA Slack Integration for Shift Notifications and Approvals
"""
import asyncio
from datetime import datetime, timedelta
from shift_service import shift_service, Shift, ShiftSignup
from slack_integration import slack_integration, ShiftNotification, ApprovalRequest

async def example_usage():
    """Demonstrate the Slack integration features"""
    
    print("🚀 YMCA Slack Integration Example")
    print("=" * 50)
    
    # Example 1: Create a new shift with Slack announcement
    print("\n1. Creating a new volunteer shift...")
    
    shift = Shift(
        title="Youth Basketball Coaching",
        description="Help coach youth basketball for ages 8-12. No experience required - we'll provide training!",
        start_time=datetime.now() + timedelta(days=3, hours=2),  # 3 days from now at 2 PM
        end_time=datetime.now() + timedelta(days=3, hours=4),    # 3 days from now at 4 PM
        location="Blue Ash YMCA Gymnasium",
        branch="Blue Ash",
        coordinator_email="sports.coordinator@ymca.org",
        skills_required=["Enthusiasm", "Team Player"],
        max_volunteers=2,
        requires_approval=True
    )
    
    try:
        shift_id = await shift_service.create_shift(shift, announce=True)
        print(f"✅ Created shift: {shift_id}")
        print(f"   Title: {shift.title}")
        print(f"   Date: {shift.start_time.strftime('%A, %B %d at %I:%M %p')}")
        print(f"   Slack announcement sent to #volunteer-announcements")
    except Exception as e:
        print(f"❌ Error creating shift: {e}")
    
    # Example 2: Volunteer signs up for shift
    print("\n2. Volunteer signing up for shift...")
    
    try:
        signup_id = await shift_service.signup_for_shift(
            shift_id=shift_id,
            volunteer_id="vol_12345",
            volunteer_name="Sarah Johnson",
            volunteer_email="sarah.johnson@email.com"
        )
        print(f"✅ Volunteer signed up: {signup_id}")
        print(f"   DM sent to Sarah Johnson")
        print(f"   Approval request sent to sports.coordinator@ymca.org")
    except Exception as e:
        print(f"❌ Error signing up: {e}")
    
    # Example 3: Coordinator approves signup
    print("\n3. Coordinator approving signup...")
    
    try:
        success = await shift_service.approve_signup(
            signup_id=signup_id,
            approver_id="coord_123",
            notes="Great to have you on the team!"
        )
        print(f"✅ Signup approved: {success}")
        print(f"   Confirmation sent to Sarah Johnson")
    except Exception as e:
        print(f"❌ Error approving: {e}")
    
    # Example 4: Send manual reminder
    print("\n4. Sending shift reminders...")
    
    try:
        reminders_sent = await shift_service.send_shift_reminders(hours_before=48)
        print(f"✅ Sent {reminders_sent} reminders")
        print(f"   Reminders sent via Slack DM and channel")
    except Exception as e:
        print(f"❌ Error sending reminders: {e}")
    
    # Example 5: Get volunteer's shifts
    print("\n5. Getting volunteer's shifts...")
    
    try:
        volunteer_shifts = await shift_service.get_volunteer_shifts("vol_12345")
        print(f"✅ Found {len(volunteer_shifts)} shifts for volunteer")
        for shift_data in volunteer_shifts:
            shift_info = shift_data["shift"]
            signup_info = shift_data["signup"]
            print(f"   - {shift_info['title']} ({signup_info['status']})")
    except Exception as e:
        print(f"❌ Error getting shifts: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Example completed! Check your Slack channels for messages.")

# Example of direct Slack integration usage
async def direct_slack_example():
    """Example of using Slack integration directly"""
    
    print("\n📱 Direct Slack Integration Example")
    print("=" * 40)
    
    # Example notification
    notification = ShiftNotification(
        shift_id="shift_789",
        volunteer_id="vol_456",
        volunteer_name="Mike Chen",
        volunteer_email="mike.chen@email.com",
        shift_title="Community Garden Cleanup",
        shift_description="Help maintain our community garden space",
        start_time=datetime.now() + timedelta(hours=26),
        end_time=datetime.now() + timedelta(hours=28),
        location="M.E. Lyons YMCA Garden",
        branch="M.E. Lyons",
        coordinator_email="garden.coordinator@ymca.org",
        skills_required=["Outdoor Work"],
        notification_type="reminder"
    )
    
    # Send channel announcement
    print("Sending channel announcement...")
    success = await slack_integration.send_channel_announcement(notification)
    print(f"Channel announcement: {'✅ Sent' if success else '❌ Failed'}")
    
    # Send direct message
    print("Sending direct message...")
    success = await slack_integration.send_direct_message(notification)
    print(f"Direct message: {'✅ Sent' if success else '❌ Failed'}")
    
    # Example approval request
    approval = ApprovalRequest(
        request_id="req_789",
        volunteer_id="vol_456",
        volunteer_name="Mike Chen",
        volunteer_email="mike.chen@email.com",
        shift_id="shift_789",
        shift_title="Community Garden Cleanup",
        request_type="schedule_change",
        request_details={
            "original_time": "2024-03-15T10:00:00",
            "requested_time": "2024-03-15T14:00:00",
            "reason": "Schedule conflict with work"
        },
        approver_email="garden.coordinator@ymca.org",
        created_at=datetime.now()
    )
    
    # Send approval request
    print("Sending approval request...")
    success = await slack_integration.send_approval_request(approval)
    print(f"Approval request: {'✅ Sent' if success else '❌ Failed'}")

async def main():
    """Run all examples"""
    print("🏃‍♀️ YMCA Volunteer System - Slack Integration Demo")
    print("This demonstrates shift notifications and approvals via Slack")
    print()
    
    # Note: These examples will only work if Slack is properly configured
    print("⚠️  Note: Slack tokens must be configured for messages to actually send")
    print("   Set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET environment variables")
    print()
    
    await example_usage()
    await direct_slack_example()
    
    print("\n🎯 Integration Features:")
    print("   ✅ Channel announcements for new shifts")
    print("   ✅ Direct message notifications to volunteers") 
    print("   ✅ Interactive approval workflow")
    print("   ✅ Automated reminder scheduling")
    print("   ✅ Real-time approval/denial via Slack buttons")
    print()
    print("📚 See SLACK_SETUP.md for complete configuration instructions")

if __name__ == "__main__":
    asyncio.run(main())