# Branch-Scoped RBAC Setup Guide

This document describes how to set up and use the branch-scoped Role-Based Access Control (RBAC) system in the Volunteer PathFinder application.

## Overview

The RBAC system implements:
- **Granular permissions** for different resources (users, volunteers, projects, analytics, etc.)
- **Branch-scoped access control** allowing different roles per YMCA branch
- **Least-privilege defaults** ensuring users only get necessary permissions
- **Permission overrides** for fine-grained access control
- **Comprehensive audit logging** for security compliance

## System Roles

The system comes with predefined roles following least-privilege principles:

### Guest
- **Scope**: Public access only
- **Permissions**: `projects.read.public`
- **Use Case**: Unauthenticated users browsing public volunteer opportunities

### Volunteer
- **Scope**: Self-service only
- **Permissions**:
  - `users.read.own`, `users.update.own`
  - `volunteers.read.own`, `volunteers.update.own`
  - `projects.read.public`
  - `analytics.read.own`
  - `rbac.read.own`
- **Use Case**: Individual volunteers managing their own profile and viewing opportunities

### Staff
- **Scope**: Own data + branch visibility
- **Permissions**:
  - All volunteer permissions
  - `volunteers.read.branch`
  - `projects.read.branch`
  - `analytics.read.branch`
  - `rbac.read.branch`
- **Use Case**: YMCA staff members who need visibility into branch operations

### Volunteer Coordinator
- **Scope**: Branch volunteer management
- **Permissions**:
  - All staff permissions
  - `users.read.branch`
  - `volunteers.manage.branch`
  - `projects.update.branch`
- **Use Case**: Coordinates volunteers within specific branches

### Branch Admin
- **Scope**: Full branch administration
- **Permissions**:
  - All coordinator permissions
  - `users.create.branch`, `users.update.branch`
  - `projects.create.branch`, `projects.delete.branch`
  - `analytics.export.branch`
  - `rbac.manage.branch`
- **Use Case**: Branch managers with full administrative control over their branch

### System Admin
- **Scope**: Global system access
- **Permissions**: All permissions with `.global` scope
- **Use Case**: IT administrators and system maintainers

## Setup Instructions

### 1. Database Setup

Run the RBAC schema SQL script to set up the necessary tables:

```sql
-- Execute in your Supabase SQL editor
\i rbac_schema.sql
```

This creates:
- `roles` - System and custom roles
- `permissions` - Granular permission definitions
- `role_permissions` - Role-to-permission mappings
- `user_branch_roles` - User role assignments per branch
- `user_permission_overrides` - Individual permission grants/denials
- `access_logs` - Audit trail for all access attempts

### 2. Application Integration

The RBAC system is automatically initialized when the application starts:

```python
# In main.py startup event
rbac_middleware, rbac_dependency = create_rbac_middleware(database)
rbac_service = RBACService(database)
await rbac_service.bootstrap_system_roles()
```

### 3. Bootstrap System Roles

System roles are automatically created on first startup. You can also manually bootstrap:

```bash
curl -X POST "http://localhost:8000/api/rbac/system/bootstrap" \
  -H "Authorization: Bearer SYSTEM_ADMIN_TOKEN"
```

## Usage Examples

### Assigning Roles

#### Assign Branch Admin Role
```python
# Via API
POST /api/rbac/users/roles/assign
{
  "user_id": "user-123",
  "role_id": "branch_admin_role_id",
  "branch": "Blue Ash",
  "expires_in_days": 365
}
```

#### Bulk Role Assignment
```python
POST /api/rbac/users/roles/bulk-assign
{
  "assignments": [
    {
      "user_id": "user-123",
      "role_id": "volunteer_coordinator_id",
      "branch": "Blue Ash"
    },
    {
      "user_id": "user-456", 
      "role_id": "staff_id",
      "branch": "M.E. Lyons"
    }
  ]
}
```

### Permission Overrides

Grant specific permission to a user:

```python
POST /api/rbac/permissions/override
{
  "user_id": "user-123",
  "permission_name": "analytics.export.branch",
  "branch": "Blue Ash",
  "granted": true,
  "reason": "Temporary access for monthly report",
  "expires_in_days": 30
}
```

### Using Middleware in Endpoints

#### Require Specific Permission
```python
from rbac_middleware import RBACMiddleware

@router.get("/api/branch/{branch}/analytics")
async def get_branch_analytics(
    branch: str,
    current_user: Dict = Depends(rbac_dependency.require_permission("analytics.read.branch"))
):
    # User has analytics.read.branch permission
    return {"analytics": "data"}
```

#### Branch-Scoped Access
```python
@router.get("/api/branch/{branch}/volunteers")
@rbac_middleware.branch_scoped("volunteers")
async def get_branch_volunteers(
    branch: str,
    target_branch: str,  # Added by middleware
    current_user: Dict = Depends(rbac_dependency.require_auth())
):
    # User has access to target_branch
    return {"volunteers": "data"}
```

#### Role-Based Access
```python
@router.post("/api/users")
@rbac_middleware.require_role(SystemRole.BRANCH_ADMIN)
async def create_user(
    user_data: UserProfile,
    current_user: Dict = Depends(rbac_dependency.require_auth())
):
    # User has branch_admin role
    return {"user": "created"}
```

## API Endpoints

### Role Management
- `GET /api/rbac/roles` - List all roles
- `POST /api/rbac/roles` - Create custom role
- `GET /api/rbac/roles/{role_id}` - Get role details
- `PUT /api/rbac/roles/{role_id}` - Update role
- `DELETE /api/rbac/roles/{role_id}` - Delete role

### User Role Assignment
- `POST /api/rbac/users/roles/assign` - Assign role to user
- `POST /api/rbac/users/roles/bulk-assign` - Bulk assign roles
- `GET /api/rbac/users/{user_id}/roles` - Get user's roles
- `DELETE /api/rbac/users/{user_id}/roles/{assignment_id}` - Revoke role

### Permission Management
- `POST /api/rbac/permissions/override` - Create permission override
- `POST /api/rbac/permissions/check` - Check user permission

### Audit & Monitoring
- `GET /api/rbac/audit/access-logs` - View access logs

## Authentication Integration

The RBAC system expects JWT tokens in the format:
```
Authorization: Bearer user_id:branch
```

For production, implement proper JWT validation:

```python
async def get_current_user(credentials: HTTPAuthorizationCredentials):
    # Decode and validate JWT
    payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
    user_id = payload.get("sub")
    branch = payload.get("branch")
    
    # Get user with RBAC context
    user = await database.get_user(user_id=user_id)
    user['rbac_context'] = await rbac_service.get_user_context(user_id)
    user['current_branch'] = branch
    
    return user
```

## Security Best Practices

1. **Least Privilege**: Start with minimal permissions and grant additional access as needed
2. **Regular Auditing**: Review access logs regularly for suspicious activity
3. **Role Rotation**: Set expiration dates on role assignments
4. **Permission Overrides**: Use sparingly and with clear justification
5. **Branch Isolation**: Ensure branch admins cannot access other branches
6. **Audit Trail**: All permission checks and role changes are logged

## Common Use Cases

### New Volunteer Registration
1. User registers → Gets `volunteer` role globally
2. Chooses primary branch → Gets `volunteer` role for that branch
3. Can read own data and public opportunities

### Staff Onboarding
1. HR assigns `staff` role for specific branch
2. Staff can view branch volunteers and projects
3. Can generate branch analytics reports

### Coordinator Promotion
1. Branch admin assigns `volunteer_coordinator` role
2. Coordinator can now manage volunteers in their branch
3. Can update project assignments and status

### Temporary Access
1. Create permission override for specific need
2. Set expiration date
3. Override automatically expires

## Troubleshooting

### Common Issues

**User can't access expected resources**
1. Check role assignments: `GET /api/rbac/users/{user_id}/roles`
2. Verify branch context in JWT token
3. Check for permission overrides that might deny access

**Permission denied errors**
1. Review access logs: `GET /api/rbac/audit/access-logs?user_id={user_id}`
2. Verify required permissions for endpoint
3. Check if role assignments are active and not expired

**Performance issues**
1. RBAC context is cached per request
2. Database queries are optimized with indexes
3. Consider caching frequently accessed permissions

### Debug Mode

Enable debug logging to trace permission checks:

```python
import logging
logging.getLogger("rbac_middleware").setLevel(logging.DEBUG)
```

## Migration from Existing System

If migrating from an existing permission system:

1. **Map existing roles** to new RBAC roles
2. **Bulk assign roles** using the bulk assignment API
3. **Test thoroughly** with different user types
4. **Monitor access logs** for denied requests
5. **Gradually remove** old permission system

This RBAC system provides enterprise-grade security with the flexibility needed for the YMCA's branch-based organizational structure.