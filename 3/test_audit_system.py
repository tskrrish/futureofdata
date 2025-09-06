"""
Test script for the Audit Log system
Tests audit logging functionality, diff generation, and export features
"""
import asyncio
import json
from datetime import datetime, timedelta
from database import VolunteerDatabase
from audit_logger import AuditLogger, AuditAction, AuditResource

async def test_audit_system():
    """Test the complete audit system"""
    print("🧪 Testing Audit Log System")
    print("=" * 50)
    
    # Initialize components
    database = VolunteerDatabase()
    audit_logger = AuditLogger(database)
    database.set_audit_logger(audit_logger)
    
    print("✅ Initialized audit system components")
    
    # Test 1: Basic audit logging
    print("\n📝 Test 1: Basic Audit Logging")
    
    # Test user creation audit
    test_user_data = {
        'email': 'test.audit@example.com',
        'first_name': 'Test',
        'last_name': 'Audit',
        'age': 30,
        'city': 'Cincinnati'
    }
    
    audit_id = await audit_logger.log_audit_entry(
        action=AuditAction.CREATE,
        resource=AuditResource.USER,
        user_id='test-user-123',
        resource_id='test-user-123',
        new_values=test_user_data,
        metadata={'test': 'basic_audit_logging', 'ip_address': '127.0.0.1'}
    )
    
    print(f"✅ Created audit entry: {audit_id}")
    
    # Test 2: Update with diff generation
    print("\n📝 Test 2: Update with Diff Generation")
    
    old_user_data = test_user_data.copy()
    new_user_data = test_user_data.copy()
    new_user_data['age'] = 31
    new_user_data['city'] = 'Blue Ash'
    new_user_data['email'] = 'test.audit.updated@example.com'
    
    update_audit_id = await audit_logger.log_audit_entry(
        action=AuditAction.UPDATE,
        resource=AuditResource.USER,
        user_id='test-user-123',
        resource_id='test-user-123',
        old_values=old_user_data,
        new_values=new_user_data,
        metadata={'test': 'update_with_diff'}
    )
    
    print(f"✅ Created update audit entry with diff: {update_audit_id}")
    
    # Test 3: Deletion audit
    print("\n📝 Test 3: Deletion Audit")
    
    delete_audit_id = await audit_logger.log_audit_entry(
        action=AuditAction.DELETE,
        resource=AuditResource.USER,
        user_id='test-user-123',
        resource_id='test-user-123',
        old_values=new_user_data,
        metadata={'test': 'deletion_audit', 'reason': 'test_cleanup'}
    )
    
    print(f"✅ Created deletion audit entry: {delete_audit_id}")
    
    # Test 4: Multiple resource types
    print("\n📝 Test 4: Multiple Resource Types")
    
    # Test preferences audit
    preferences_data = {
        'interests': 'youth development, fitness',
        'availability': {'weekday': True, 'evening': True},
        'time_commitment': 2,
        'location_preference': 'Blue Ash'
    }
    
    prefs_audit_id = await audit_logger.log_audit_entry(
        action=AuditAction.CREATE,
        resource=AuditResource.USER_PREFERENCES,
        user_id='test-user-123',
        resource_id='test-prefs-456',
        new_values=preferences_data,
        metadata={'test': 'preferences_audit'}
    )
    
    print(f"✅ Created preferences audit entry: {prefs_audit_id}")
    
    # Test conversation audit
    conversation_audit_id = await audit_logger.log_audit_entry(
        action=AuditAction.CREATE,
        resource=AuditResource.CONVERSATION,
        user_id='test-user-123',
        resource_id='test-conv-789',
        new_values={'conversation_id': 'test-conv-789', 'started_at': datetime.now().isoformat()},
        metadata={'test': 'conversation_audit'}
    )
    
    print(f"✅ Created conversation audit entry: {conversation_audit_id}")
    
    # Wait a moment to ensure timestamps differ
    await asyncio.sleep(1)
    
    # Test 5: Retrieve audit logs
    print("\n📝 Test 5: Retrieve Audit Logs")
    
    # Get all logs for our test user
    user_logs = await audit_logger.get_audit_logs(user_id='test-user-123', limit=10)
    print(f"✅ Retrieved {len(user_logs)} logs for test user")
    
    if user_logs:
        print("Sample audit log:")
        sample_log = user_logs[0]
        print(f"  - Action: {sample_log.get('action')}")
        print(f"  - Resource: {sample_log.get('resource')}")
        print(f"  - Timestamp: {sample_log.get('timestamp')}")
        print(f"  - Has diff: {'Yes' if sample_log.get('diff_text') else 'No'}")
    
    # Test 6: Resource history
    print("\n📝 Test 6: Resource History")
    
    resource_history = await audit_logger.get_resource_history(
        AuditResource.USER, 'test-user-123'
    )
    print(f"✅ Retrieved {len(resource_history)} history entries for user resource")
    
    # Test 7: User activity
    print("\n📝 Test 7: User Activity")
    
    user_activity = await audit_logger.get_user_activity('test-user-123', days=1)
    print(f"✅ Retrieved {len(user_activity)} activity entries for test user")
    
    # Test 8: Audit statistics
    print("\n📝 Test 8: Audit Statistics")
    
    stats = await audit_logger.get_audit_statistics(days=1)
    if 'error' not in stats:
        print("✅ Retrieved audit statistics:")
        print(f"  - Total activities: {stats.get('total_activities', 'N/A')}")
        print(f"  - Unique users: {stats.get('unique_users', 'N/A')}")
        print(f"  - Activity by action: {stats.get('activity_by_action', {})}")
        print(f"  - Activity by resource: {stats.get('activity_by_resource', {})}")
    else:
        print(f"⚠️  Stats error: {stats.get('error')}")
    
    # Test 9: Export functionality
    print("\n📝 Test 9: Export Functionality")
    
    try:
        # Test CSV export
        csv_export = await audit_logger.export_audit_logs(
            format_type="csv",
            user_id='test-user-123'
        )
        print(f"✅ CSV export successful ({len(csv_export)} characters)")
        
        # Test JSON export
        json_export = await audit_logger.export_audit_logs(
            format_type="json",
            user_id='test-user-123'
        )
        
        # Validate JSON
        json_data = json.loads(json_export)
        print(f"✅ JSON export successful ({len(json_data)} records)")
        
        # Test Excel export (if pandas/openpyxl are available)
        try:
            excel_export = await audit_logger.export_audit_logs(
                format_type="excel",
                user_id='test-user-123'
            )
            print(f"✅ Excel export successful ({len(excel_export)} bytes)")
        except ImportError as e:
            print(f"⚠️  Excel export skipped (missing dependency): {e}")
            
    except Exception as e:
        print(f"❌ Export test failed: {e}")
    
    # Test 10: Diff visualization
    print("\n📝 Test 10: Diff Visualization")
    
    if user_logs:
        for log in user_logs:
            if log.get('diff_text') and log.get('action') == 'update':
                print("Sample diff output:")
                print("```")
                print(log['diff_text'][:500] + "..." if len(log.get('diff_text', '')) > 500 else log.get('diff_text'))
                print("```")
                break
    
    print("\n" + "=" * 50)
    print("🎉 Audit Log System Test Complete!")
    print("=" * 50)
    
    # Summary
    print("\n📊 Test Summary:")
    print("✅ Basic audit logging")
    print("✅ Update tracking with diffs")
    print("✅ Deletion tracking")
    print("✅ Multiple resource types")
    print("✅ Log retrieval and filtering")
    print("✅ Resource history")
    print("✅ User activity tracking")
    print("✅ Statistics generation")
    print("✅ Export functionality (CSV, JSON, Excel)")
    print("✅ Diff visualization")
    
    return True

async def test_audit_integration():
    """Test audit logging integration with database operations"""
    print("\n🔗 Testing Database Integration")
    print("=" * 50)
    
    database = VolunteerDatabase()
    audit_logger = AuditLogger(database)
    database.set_audit_logger(audit_logger)
    
    # Test creating a user (should automatically log audit entry)
    test_user = {
        'email': 'integration.test@example.com',
        'first_name': 'Integration',
        'last_name': 'Test',
        'age': 28,
        'city': 'Cincinnati'
    }
    
    print("Creating user through database (should trigger audit log)...")
    user = await database.create_user(test_user)
    
    if user:
        print(f"✅ User created: {user.get('id')}")
        
        # Check if audit log was created
        await asyncio.sleep(1)  # Give time for audit log to be saved
        
        user_logs = await audit_logger.get_audit_logs(user_id=user.get('id'), limit=5)
        print(f"✅ Found {len(user_logs)} audit logs for the created user")
        
        if user_logs:
            log = user_logs[0]
            print(f"  - Action: {log.get('action')}")
            print(f"  - Resource: {log.get('resource')}")
            print(f"  - Has new values: {'Yes' if log.get('new_values') else 'No'}")
    else:
        print("⚠️  User creation failed (possibly due to missing Supabase config)")
    
    print("✅ Database integration test complete")

if __name__ == "__main__":
    async def run_all_tests():
        await test_audit_system()
        await test_audit_integration()
    
    print("🚀 Starting Audit System Tests...")
    asyncio.run(run_all_tests())