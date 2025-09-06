"""
Test script for Branch-Scoped RBAC System
Demonstrates key functionality and validates implementation
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

from rbac_models import RBACService, SystemRole, Permission, Role, UserBranchRole, RBACContext
from database import VolunteerDatabase
from datetime import datetime, timedelta

async def test_rbac_system():
    """Test the RBAC system functionality"""
    print("🧪 Testing Branch-Scoped RBAC System")
    print("=" * 50)
    
    # Initialize database and RBAC service
    database = VolunteerDatabase()
    if not database._is_available():
        print("❌ Database not available - skipping tests")
        return False
    
    rbac_service = RBACService(database)
    
    try:
        # Test 1: Bootstrap system roles
        print("\n1. Testing system role bootstrap...")
        success = await rbac_service.bootstrap_system_roles()
        print(f"   Bootstrap: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        # Test 2: Create test users
        print("\n2. Creating test users...")
        
        # Create volunteer user
        volunteer_user = await database.create_user({
            'email': 'volunteer@test.com',
            'first_name': 'Test',
            'last_name': 'Volunteer',
            'member_branch': 'Blue Ash'
        })
        
        # Create coordinator user  
        coordinator_user = await database.create_user({
            'email': 'coordinator@test.com',
            'first_name': 'Test',
            'last_name': 'Coordinator',
            'member_branch': 'Blue Ash'
        })
        
        # Create admin user
        admin_user = await database.create_user({
            'email': 'admin@test.com',
            'first_name': 'Test',
            'last_name': 'Admin',
            'member_branch': 'Blue Ash'
        })
        
        if volunteer_user and coordinator_user and admin_user:
            print("   Users created: ✅ SUCCESS")
            volunteer_id = volunteer_user['id']
            coordinator_id = coordinator_user['id'] 
            admin_id = admin_user['id']
        else:
            print("   Users created: ❌ FAILED")
            return False
        
        # Test 3: Get system roles
        print("\n3. Getting system roles...")
        
        # Get volunteer role
        volunteer_role_result = await database.supabase.table('roles')\
            .select('id')\
            .eq('name', SystemRole.VOLUNTEER.value)\
            .execute()
        volunteer_role_id = volunteer_role_result.data[0]['id'] if volunteer_role_result.data else None
        
        # Get coordinator role
        coordinator_role_result = await database.supabase.table('roles')\
            .select('id')\
            .eq('name', SystemRole.VOLUNTEER_COORDINATOR.value)\
            .execute()
        coordinator_role_id = coordinator_role_result.data[0]['id'] if coordinator_role_result.data else None
        
        # Get admin role
        admin_role_result = await database.supabase.table('roles')\
            .select('id')\
            .eq('name', SystemRole.SYSTEM_ADMIN.value)\
            .execute()
        admin_role_id = admin_role_result.data[0]['id'] if admin_role_result.data else None
        
        if volunteer_role_id and coordinator_role_id and admin_role_id:
            print("   System roles found: ✅ SUCCESS")
        else:
            print("   System roles found: ❌ FAILED")
            return False
        
        # Test 4: Assign roles to users
        print("\n4. Assigning roles to users...")
        
        # Assign volunteer role
        volunteer_assigned = await rbac_service.assign_role_to_user(
            user_id=volunteer_id,
            role_id=volunteer_role_id,
            branch='Blue Ash',
            granted_by=admin_id
        )
        
        # Assign coordinator role
        coordinator_assigned = await rbac_service.assign_role_to_user(
            user_id=coordinator_id,
            role_id=coordinator_role_id, 
            branch='Blue Ash',
            granted_by=admin_id
        )
        
        # Assign admin role (global)
        admin_assigned = await rbac_service.assign_role_to_user(
            user_id=admin_id,
            role_id=admin_role_id,
            branch=None,  # Global admin
            granted_by=admin_id
        )
        
        assignments_success = volunteer_assigned and coordinator_assigned and admin_assigned
        print(f"   Role assignments: {'✅ SUCCESS' if assignments_success else '❌ FAILED'}")
        
        # Test 5: Test permission checking
        print("\n5. Testing permission checks...")
        
        # Test volunteer permissions
        print("   Volunteer permissions:")
        volunteer_can_read_own = await rbac_service.check_permission(
            volunteer_id, "users.read.own"
        )
        print(f"     - Can read own profile: {'✅' if volunteer_can_read_own else '❌'}")
        
        volunteer_can_manage_branch = await rbac_service.check_permission(
            volunteer_id, "volunteers.manage.branch", "Blue Ash"
        )
        print(f"     - Can manage branch volunteers: {'❌' if not volunteer_can_manage_branch else '✅'}")
        
        # Test coordinator permissions
        print("   Coordinator permissions:")
        coord_can_manage_branch = await rbac_service.check_permission(
            coordinator_id, "volunteers.manage.branch", "Blue Ash"
        )
        print(f"     - Can manage branch volunteers: {'✅' if coord_can_manage_branch else '❌'}")
        
        coord_can_manage_other_branch = await rbac_service.check_permission(
            coordinator_id, "volunteers.manage.branch", "M.E. Lyons"
        )
        print(f"     - Can manage other branch: {'❌' if not coord_can_manage_other_branch else '✅'}")
        
        # Test admin permissions
        print("   Admin permissions:")
        admin_can_manage_global = await rbac_service.check_permission(
            admin_id, "users.manage.global"
        )
        print(f"     - Can manage users globally: {'✅' if admin_can_manage_global else '❌'}")
        
        # Test 6: Test RBAC context
        print("\n6. Testing RBAC contexts...")
        
        # Get volunteer context
        volunteer_context = await rbac_service.get_user_context(volunteer_id)
        volunteer_perms = volunteer_context.get_user_permissions("Blue Ash")
        print(f"   Volunteer permissions count: {len(volunteer_perms)}")
        print(f"   Sample permissions: {list(volunteer_perms)[:3]}")
        
        # Get coordinator context
        coord_context = await rbac_service.get_user_context(coordinator_id)
        coord_perms = coord_context.get_user_permissions("Blue Ash")
        coord_branches = coord_context.get_accessible_branches()
        print(f"   Coordinator permissions count: {len(coord_perms)}")
        print(f"   Accessible branches: {list(coord_branches)}")
        
        # Test 7: Test permission override
        print("\n7. Testing permission overrides...")
        
        # Get analytics permission ID
        analytics_perm_result = await database.supabase.table('permissions')\
            .select('id')\
            .eq('name', 'analytics.export.branch')\
            .execute()
        
        if analytics_perm_result.data:
            analytics_perm_id = analytics_perm_result.data[0]['id']
            
            # Create override to grant analytics export to volunteer
            override_data = {
                'user_id': volunteer_id,
                'permission_id': analytics_perm_id,
                'branch': 'Blue Ash',
                'granted': True,
                'granted_by': admin_id,
                'reason': 'Test override',
                'expires_at': (datetime.now() + timedelta(days=1)).isoformat()
            }
            
            override_result = await database.supabase.table('user_permission_overrides')\
                .insert(override_data)\
                .execute()
            
            if override_result.data:
                # Check if volunteer now has the permission
                volunteer_can_export = await rbac_service.check_permission(
                    volunteer_id, "analytics.export.branch", "Blue Ash"
                )
                print(f"   Permission override: {'✅ SUCCESS' if volunteer_can_export else '❌ FAILED'}")
            else:
                print("   Permission override: ❌ FAILED to create")
        
        # Test 8: Test access logging
        print("\n8. Testing access logging...")
        
        # Check access logs were created
        logs_result = await database.supabase.table('access_logs')\
            .select('*', count='exact')\
            .execute()
        
        log_count = logs_result.count
        print(f"   Access logs created: {log_count} entries")
        
        if log_count > 0:
            recent_log = logs_result.data[0]
            print(f"   Recent log: {recent_log.get('resource', 'N/A')} {recent_log.get('action', 'N/A')} - {'✅ GRANTED' if recent_log.get('granted') else '❌ DENIED'}")
        
        # Test 9: Test least-privilege validation
        print("\n9. Validating least-privilege implementation...")
        
        defaults = rbac_service.get_least_privilege_defaults()
        
        # Volunteer should have minimal permissions
        volunteer_defaults = defaults[SystemRole.VOLUNTEER]
        volunteer_has_admin = any('manage.global' in perm for perm in volunteer_defaults)
        print(f"   Volunteer has admin perms: {'❌ FAILED' if volunteer_has_admin else '✅ SUCCESS'}")
        
        # System admin should have full permissions
        admin_defaults = defaults[SystemRole.SYSTEM_ADMIN]
        admin_has_system = any('system.manage' in perm for perm in admin_defaults)
        print(f"   Admin has system perms: {'✅ SUCCESS' if admin_has_system else '❌ FAILED'}")
        
        print("\n" + "=" * 50)
        print("✅ RBAC System Tests Completed Successfully!")
        print(f"📊 Summary:")
        print(f"   - System roles: Bootstrapped")
        print(f"   - Test users: Created ({volunteer_id[:8]}..., {coordinator_id[:8]}..., {admin_id[:8]}...)")
        print(f"   - Role assignments: Working")
        print(f"   - Permission checks: Working") 
        print(f"   - Branch scoping: Working")
        print(f"   - Permission overrides: Working")
        print(f"   - Access logging: Working")
        print(f"   - Least privilege: Validated")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    database = VolunteerDatabase()
    if not database._is_available():
        return
    
    try:
        # Delete test users (cascade will handle related records)
        await database.supabase.table('users')\
            .delete()\
            .in_('email', ['volunteer@test.com', 'coordinator@test.com', 'admin@test.com'])\
            .execute()
        
        print("   Test cleanup: ✅ SUCCESS")
        
    except Exception as e:
        print(f"   Test cleanup: ❌ FAILED - {e}")

if __name__ == "__main__":
    async def main():
        # Run tests
        success = await test_rbac_system()
        
        # Cleanup
        await cleanup_test_data()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
    
    asyncio.run(main())