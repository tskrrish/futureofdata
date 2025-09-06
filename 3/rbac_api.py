"""
RBAC API Endpoints for Volunteer PathFinder
Provides endpoints for managing branch-scoped roles and permissions
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from rbac_models import (
    RBACService, SystemRole, Role, Permission, UserBranchRole, 
    PermissionOverride, AccessLogEntry, RBACContext
)
from rbac_middleware import RBACMiddleware, RBACDependency, create_rbac_middleware
from database import VolunteerDatabase

logger = logging.getLogger(__name__)

# Request/Response models
class CreateRoleRequest(BaseModel):
    name: str = Field(..., description="Role name")
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list, description="Permission names")

class UpdateRoleRequest(BaseModel):
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class AssignRoleRequest(BaseModel):
    user_id: str
    role_id: str
    branch: Optional[str] = None
    expires_in_days: Optional[int] = None

class PermissionOverrideRequest(BaseModel):
    user_id: str
    permission_name: str
    branch: Optional[str] = None
    granted: bool
    reason: Optional[str] = None
    expires_in_days: Optional[int] = None

class BulkRoleAssignmentRequest(BaseModel):
    assignments: List[AssignRoleRequest]

class RoleResponse(BaseModel):
    role: Role
    user_count: int = 0
    branch_assignments: Dict[str, int] = Field(default_factory=dict)

class UserRoleResponse(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    roles: List[UserBranchRole]
    effective_permissions: Dict[str, List[str]] = Field(default_factory=dict)
    accessible_branches: List[str] = Field(default_factory=list)

class PermissionCheckRequest(BaseModel):
    user_id: str
    permission: str
    branch: Optional[str] = None

class AccessLogResponse(BaseModel):
    logs: List[AccessLogEntry]
    total: int
    page: int
    per_page: int

def create_rbac_router(database: VolunteerDatabase) -> APIRouter:
    """Create RBAC API router"""
    router = APIRouter(prefix="/api/rbac", tags=["RBAC"])
    
    # Create RBAC middleware and dependencies
    rbac_middleware, rbac_dependency = create_rbac_middleware(database)
    rbac_service = RBACService(database)
    
    # Helper functions
    async def get_current_user_admin():
        """Dependency that requires RBAC admin permissions"""
        return rbac_dependency.require_permission("rbac.manage.global")()
    
    async def get_current_user_branch_admin(branch: str = Path(...)):
        """Dependency that requires branch RBAC admin permissions"""
        return rbac_dependency.require_permission("rbac.manage.branch", branch)()
    
    # System initialization
    @router.post("/system/bootstrap")
    async def bootstrap_system_roles(
        current_user: Dict[str, Any] = Depends(get_current_user_admin)
    ):
        """Bootstrap system with default roles and permissions"""
        try:
            success = await rbac_service.bootstrap_system_roles()
            
            if success:
                return JSONResponse(content={
                    "success": True,
                    "message": "System roles bootstrapped successfully"
                })
            else:
                raise HTTPException(status_code=500, detail="Failed to bootstrap system roles")
                
        except Exception as e:
            logger.error(f"Error bootstrapping system: {e}")
            raise HTTPException(status_code=500, detail="System bootstrap failed")
    
    # Role management
    @router.get("/roles")
    async def list_roles(
        include_permissions: bool = Query(False),
        current_user: Dict[str, Any] = Depends(rbac_dependency.require_auth())
    ) -> List[RoleResponse]:
        """List all roles with optional permission details"""
        try:
            # Check permissions
            can_read_global = await rbac_middleware.check_permission(
                current_user, "rbac.read.global"
            )
            can_read_branch = await rbac_middleware.check_permission(
                current_user, "rbac.read.branch"
            )
            can_read_own = await rbac_middleware.check_permission(
                current_user, "rbac.read.own"
            )
            
            if not (can_read_global or can_read_branch or can_read_own):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            # Get roles from database
            result = await database.supabase.table('roles').select('*').execute()
            roles_data = result.data
            
            responses = []
            for role_data in roles_data:
                role = Role(**role_data)
                
                # Get permissions if requested
                if include_permissions:
                    role = await rbac_service.get_role_by_id(role.id)
                
                # Get user count and branch assignments
                user_count_result = await database.supabase.table('user_branch_roles')\
                    .select('user_id, branch', count='exact')\
                    .eq('role_id', role.id)\
                    .eq('is_active', True)\
                    .execute()
                
                user_count = user_count_result.count
                
                # Count by branch
                branch_assignments = {}
                for assignment in user_count_result.data:
                    branch = assignment.get('branch', 'Global')
                    branch_assignments[branch] = branch_assignments.get(branch, 0) + 1
                
                responses.append(RoleResponse(
                    role=role,
                    user_count=user_count,
                    branch_assignments=branch_assignments
                ))
            
            return responses
            
        except Exception as e:
            logger.error(f"Error listing roles: {e}")
            raise HTTPException(status_code=500, detail="Failed to list roles")
    
    @router.post("/roles")
    async def create_role(
        request: CreateRoleRequest,
        current_user: Dict[str, Any] = Depends(get_current_user_admin)
    ) -> RoleResponse:
        """Create a new role"""
        try:
            role = await rbac_service.create_role(
                name=request.name,
                description=request.description,
                permissions=request.permissions
            )
            
            return RoleResponse(role=role)
            
        except Exception as e:
            logger.error(f"Error creating role: {e}")
            if "unique" in str(e).lower():
                raise HTTPException(status_code=400, detail="Role name already exists")
            raise HTTPException(status_code=500, detail="Failed to create role")
    
    @router.get("/roles/{role_id}")
    async def get_role(
        role_id: str,
        current_user: Dict[str, Any] = Depends(rbac_dependency.require_auth())
    ) -> RoleResponse:
        """Get role by ID with full details"""
        try:
            role = await rbac_service.get_role_by_id(role_id)
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")
            
            # Check if user can read this role
            can_read = await rbac_middleware.check_permission(
                current_user, "rbac.read.global"
            ) or await rbac_middleware.check_permission(
                current_user, "rbac.read.branch"
            )
            
            if not can_read:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return RoleResponse(role=role)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting role: {e}")
            raise HTTPException(status_code=500, detail="Failed to get role")
    
    @router.put("/roles/{role_id}")
    async def update_role(
        role_id: str,
        request: UpdateRoleRequest,
        current_user: Dict[str, Any] = Depends(get_current_user_admin)
    ) -> RoleResponse:
        """Update role"""
        try:
            # Get existing role
            role = await rbac_service.get_role_by_id(role_id)
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")
            
            if role.is_system_role:
                raise HTTPException(status_code=400, detail="Cannot modify system roles")
            
            update_data = {}
            if request.description is not None:
                update_data['description'] = request.description
            
            if update_data:
                # Update role basic info
                result = await database.supabase.table('roles')\
                    .update(update_data)\
                    .eq('id', role_id)\
                    .execute()
            
            # Update permissions if provided
            if request.permissions is not None:
                # Remove existing permissions
                await database.supabase.table('role_permissions')\
                    .delete()\
                    .eq('role_id', role_id)\
                    .execute()
                
                # Add new permissions
                await rbac_service.add_permissions_to_role(role_id, request.permissions)
            
            # Get updated role
            updated_role = await rbac_service.get_role_by_id(role_id)
            return RoleResponse(role=updated_role)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating role: {e}")
            raise HTTPException(status_code=500, detail="Failed to update role")
    
    @router.delete("/roles/{role_id}")
    async def delete_role(
        role_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user_admin)
    ):
        """Delete role"""
        try:
            # Get role
            role = await rbac_service.get_role_by_id(role_id)
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")
            
            if role.is_system_role:
                raise HTTPException(status_code=400, detail="Cannot delete system roles")
            
            # Check if role is assigned to users
            assignments_result = await database.supabase.table('user_branch_roles')\
                .select('id', count='exact')\
                .eq('role_id', role_id)\
                .eq('is_active', True)\
                .execute()
            
            if assignments_result.count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot delete role with {assignments_result.count} active assignments"
                )
            
            # Delete role
            await database.supabase.table('roles')\
                .delete()\
                .eq('id', role_id)\
                .execute()
            
            return JSONResponse(content={"success": True, "message": "Role deleted"})
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting role: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete role")
    
    # User role management
    @router.post("/users/roles/assign")
    async def assign_role_to_user(
        request: AssignRoleRequest,
        current_user: Dict[str, Any] = Depends(rbac_dependency.require_auth())
    ):
        """Assign role to user for specific branch"""
        try:
            # Check permissions - can assign if global admin or branch admin
            can_assign_global = await rbac_middleware.check_permission(
                current_user, "rbac.manage.global"
            )
            can_assign_branch = await rbac_middleware.check_permission(
                current_user, "rbac.manage.branch", request.branch
            )
            
            if not (can_assign_global or can_assign_branch):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            # Calculate expiration
            expires_at = None
            if request.expires_in_days:
                expires_at = datetime.now() + timedelta(days=request.expires_in_days)
            
            # Assign role
            success = await rbac_service.assign_role_to_user(
                user_id=request.user_id,
                role_id=request.role_id,
                branch=request.branch,
                granted_by=current_user['id'],
                expires_at=expires_at
            )
            
            if success:
                return JSONResponse(content={"success": True, "message": "Role assigned"})
            else:
                raise HTTPException(status_code=400, detail="Failed to assign role")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error assigning role: {e}")
            raise HTTPException(status_code=500, detail="Role assignment failed")
    
    @router.post("/users/roles/bulk-assign")
    async def bulk_assign_roles(
        request: BulkRoleAssignmentRequest,
        current_user: Dict[str, Any] = Depends(get_current_user_admin)
    ):
        """Bulk assign roles to multiple users"""
        try:
            results = []
            for assignment in request.assignments:
                try:
                    expires_at = None
                    if assignment.expires_in_days:
                        expires_at = datetime.now() + timedelta(days=assignment.expires_in_days)
                    
                    success = await rbac_service.assign_role_to_user(
                        user_id=assignment.user_id,
                        role_id=assignment.role_id,
                        branch=assignment.branch,
                        granted_by=current_user['id'],
                        expires_at=expires_at
                    )
                    
                    results.append({
                        "user_id": assignment.user_id,
                        "role_id": assignment.role_id,
                        "branch": assignment.branch,
                        "success": success
                    })
                    
                except Exception as e:
                    results.append({
                        "user_id": assignment.user_id,
                        "role_id": assignment.role_id,
                        "branch": assignment.branch,
                        "success": False,
                        "error": str(e)
                    })
            
            return JSONResponse(content={"results": results})
            
        except Exception as e:
            logger.error(f"Error in bulk role assignment: {e}")
            raise HTTPException(status_code=500, detail="Bulk assignment failed")
    
    @router.get("/users/{user_id}/roles")
    async def get_user_roles(
        user_id: str,
        current_user: Dict[str, Any] = Depends(rbac_dependency.require_auth())
    ) -> UserRoleResponse:
        """Get user's roles and effective permissions"""
        try:
            # Check if user can view this user's roles
            is_self = current_user['id'] == user_id
            can_read_global = await rbac_middleware.check_permission(
                current_user, "rbac.read.global"
            )
            can_read_branch = await rbac_middleware.check_permission(
                current_user, "rbac.read.branch"
            )
            
            if not (is_self or can_read_global or can_read_branch):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            # Get RBAC context
            context = await rbac_service.get_user_context(user_id)
            
            # Get user info
            user = await database.get_user(user_id=user_id)
            user_name = None
            if user:
                user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            
            # Get effective permissions by branch
            effective_permissions = {}
            accessible_branches = list(context.get_accessible_branches())
            
            for branch in accessible_branches + [None]:  # Include global permissions
                permissions = context.get_user_permissions(branch)
                branch_key = branch or "Global"
                effective_permissions[branch_key] = sorted(list(permissions))
            
            return UserRoleResponse(
                user_id=user_id,
                user_name=user_name,
                roles=context.user_roles,
                effective_permissions=effective_permissions,
                accessible_branches=accessible_branches
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user roles")
    
    @router.delete("/users/{user_id}/roles/{role_assignment_id}")
    async def revoke_user_role(
        user_id: str,
        role_assignment_id: str,
        current_user: Dict[str, Any] = Depends(rbac_dependency.require_auth())
    ):
        """Revoke role assignment from user"""
        try:
            # Get assignment details
            assignment_result = await database.supabase.table('user_branch_roles')\
                .select('*')\
                .eq('id', role_assignment_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not assignment_result.data:
                raise HTTPException(status_code=404, detail="Role assignment not found")
            
            assignment = assignment_result.data[0]
            
            # Check permissions
            can_revoke_global = await rbac_middleware.check_permission(
                current_user, "rbac.manage.global"
            )
            can_revoke_branch = await rbac_middleware.check_permission(
                current_user, "rbac.manage.branch", assignment['branch']
            )
            
            if not (can_revoke_global or can_revoke_branch):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            # Revoke (deactivate) assignment
            await database.supabase.table('user_branch_roles')\
                .update({'is_active': False})\
                .eq('id', role_assignment_id)\
                .execute()
            
            return JSONResponse(content={"success": True, "message": "Role revoked"})
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error revoking role: {e}")
            raise HTTPException(status_code=500, detail="Failed to revoke role")
    
    # Permission overrides
    @router.post("/permissions/override")
    async def create_permission_override(
        request: PermissionOverrideRequest,
        current_user: Dict[str, Any] = Depends(rbac_dependency.require_auth())
    ):
        """Create permission override for user"""
        try:
            # Check permissions
            can_override_global = await rbac_middleware.check_permission(
                current_user, "rbac.manage.global"
            )
            can_override_branch = await rbac_middleware.check_permission(
                current_user, "rbac.manage.branch", request.branch
            )
            
            if not (can_override_global or can_override_branch):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            # Get permission ID
            perm_result = await database.supabase.table('permissions')\
                .select('id')\
                .eq('name', request.permission_name)\
                .execute()
            
            if not perm_result.data:
                raise HTTPException(status_code=404, detail="Permission not found")
            
            permission_id = perm_result.data[0]['id']
            
            # Calculate expiration
            expires_at = None
            if request.expires_in_days:
                expires_at = datetime.now() + timedelta(days=request.expires_in_days)
            
            # Create override
            override_data = {
                'user_id': request.user_id,
                'permission_id': permission_id,
                'branch': request.branch,
                'granted': request.granted,
                'granted_by': current_user['id'],
                'reason': request.reason,
                'expires_at': expires_at.isoformat() if expires_at else None
            }
            
            result = await database.supabase.table('user_permission_overrides')\
                .upsert(override_data)\
                .execute()
            
            if result.data:
                return JSONResponse(content={"success": True, "message": "Permission override created"})
            else:
                raise HTTPException(status_code=400, detail="Failed to create override")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating permission override: {e}")
            raise HTTPException(status_code=500, detail="Permission override failed")
    
    # Permission checking
    @router.post("/permissions/check")
    async def check_permission(
        request: PermissionCheckRequest,
        current_user: Dict[str, Any] = Depends(rbac_dependency.require_auth())
    ) -> Dict[str, Any]:
        """Check if user has specific permission"""
        try:
            # Only allow checking own permissions or if admin
            is_self = current_user['id'] == request.user_id
            is_admin = await rbac_middleware.check_permission(
                current_user, "rbac.read.global"
            ) or await rbac_middleware.check_permission(
                current_user, "rbac.read.branch"
            )
            
            if not (is_self or is_admin):
                raise HTTPException(status_code=403, detail="Can only check own permissions")
            
            has_permission = await rbac_service.check_permission(
                user_id=request.user_id,
                permission=request.permission,
                branch=request.branch
            )
            
            return {
                "user_id": request.user_id,
                "permission": request.permission,
                "branch": request.branch,
                "granted": has_permission
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            raise HTTPException(status_code=500, detail="Permission check failed")
    
    # Audit logs
    @router.get("/audit/access-logs")
    async def get_access_logs(
        user_id: Optional[str] = Query(None),
        resource: Optional[str] = Query(None),
        branch: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        per_page: int = Query(50, ge=1, le=1000),
        current_user: Dict[str, Any] = Depends(rbac_dependency.require_auth())
    ) -> AccessLogResponse:
        """Get access logs with filtering"""
        try:
            # Check permissions
            can_read_global = await rbac_middleware.check_permission(
                current_user, "analytics.read.global"
            )
            can_read_branch = await rbac_middleware.check_permission(
                current_user, "analytics.read.branch", branch
            )
            can_read_own = current_user['id'] == user_id and user_id is not None
            
            if not (can_read_global or can_read_branch or can_read_own):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            # Build query
            query = database.supabase.table('access_logs').select('*')
            
            if user_id:
                query = query.eq('user_id', user_id)
            if resource:
                query = query.eq('resource', resource)
            if branch:
                query = query.eq('branch', branch)
            
            # Get total count
            count_result = await query.select('id', count='exact').execute()
            total = count_result.count
            
            # Get paginated results
            offset = (page - 1) * per_page
            result = await query.order('created_at', desc=True)\
                .range(offset, offset + per_page - 1)\
                .execute()
            
            logs = [AccessLogEntry(**log_data) for log_data in result.data]
            
            return AccessLogResponse(
                logs=logs,
                total=total,
                page=page,
                per_page=per_page
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting access logs: {e}")
            raise HTTPException(status_code=500, detail="Failed to get access logs")
    
    return router