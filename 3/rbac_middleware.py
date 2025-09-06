"""
RBAC Authorization Middleware for Volunteer PathFinder
Implements branch-scoped access control with least-privilege enforcement
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable, List, Dict, Any
import functools
import logging
from datetime import datetime

from rbac_models import RBACService, SystemRole
from database import VolunteerDatabase

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)

class RBACMiddleware:
    """Middleware for RBAC authorization"""
    
    def __init__(self, database: VolunteerDatabase):
        self.database = database
        self.rbac_service = RBACService(database)
        self._user_cache: Dict[str, Dict[str, Any]] = {}
        
    async def get_current_user(self, 
                             credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
                             ) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        if not credentials:
            return None
            
        try:
            # In a real implementation, you would decode and validate the JWT token
            # For this example, we'll use a simple token format: "user_id:branch"
            token_parts = credentials.credentials.split(":")
            user_id = token_parts[0]
            
            # Get user from database
            user = await self.database.get_user(user_id=user_id)
            if not user:
                return None
                
            # Add RBAC context
            user['rbac_context'] = await self.rbac_service.get_user_context(user_id)
            user['current_branch'] = token_parts[1] if len(token_parts) > 1 else user.get('member_branch')
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    async def check_permission(self, user: Dict[str, Any], permission: str, 
                              branch: Optional[str] = None) -> bool:
        """Check if user has permission"""
        if not user:
            return False
            
        try:
            rbac_context = user.get('rbac_context')
            if not rbac_context:
                return False
                
            target_branch = branch or user.get('current_branch')
            has_permission = rbac_context.has_permission(permission, target_branch)
            
            # Log access attempt
            await self.rbac_service.log_access(
                resource=permission.split('.')[0] if '.' in permission else 'unknown',
                action=permission.split('.')[1] if '.' in permission else 'unknown',
                user_id=user['id'],
                branch=target_branch,
                granted=has_permission,
                reason=f"Middleware permission check: {permission}"
            )
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    def require_permission(self, permission: str, branch: Optional[str] = None):
        """Decorator to require specific permission"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract current user from kwargs or get it
                current_user = kwargs.get('current_user')
                if not current_user:
                    # Try to get from request context
                    request = kwargs.get('request')
                    if request and hasattr(request.state, 'user'):
                        current_user = request.state.user
                
                if not current_user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                # Check permission
                has_permission = await self.check_permission(current_user, permission, branch)
                if not has_permission:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Insufficient permissions: {permission} required"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_role(self, role: SystemRole, branch: Optional[str] = None):
        """Decorator to require specific role"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                # Check if user has role
                rbac_context = current_user.get('rbac_context')
                if not rbac_context:
                    raise HTTPException(status_code=403, detail="No RBAC context")
                
                target_branch = branch or current_user.get('current_branch')
                has_role = any(
                    ur.role and ur.role.name == role.value and 
                    (ur.branch is None or ur.branch == target_branch) and ur.is_valid()
                    for ur in rbac_context.user_roles
                )
                
                if not has_role:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Role {role.value} required for branch {target_branch}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def branch_scoped(self, resource: str):
        """Decorator to enforce branch-scoped access"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                # Get target branch from request
                request = kwargs.get('request')
                target_branch = None
                
                if request:
                    # Check path parameters
                    path_params = getattr(request, 'path_params', {})
                    target_branch = path_params.get('branch')
                    
                    # Check query parameters
                    if not target_branch:
                        query_params = dict(request.query_params)
                        target_branch = query_params.get('branch')
                
                # Use user's default branch if no target specified
                if not target_branch:
                    target_branch = current_user.get('current_branch')
                
                # Check if user has access to target branch
                rbac_context = current_user.get('rbac_context')
                if rbac_context and target_branch:
                    accessible_branches = rbac_context.get_accessible_branches()
                    
                    # System admin has access to all branches
                    is_system_admin = any(
                        ur.role and ur.role.name == SystemRole.SYSTEM_ADMIN.value and ur.is_valid()
                        for ur in rbac_context.user_roles
                    )
                    
                    if not is_system_admin and target_branch not in accessible_branches:
                        raise HTTPException(
                            status_code=403,
                            detail=f"Access denied to branch: {target_branch}"
                        )
                
                # Add branch context to kwargs
                kwargs['target_branch'] = target_branch
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

class RBACDependency:
    """FastAPI dependency for RBAC"""
    
    def __init__(self, middleware: RBACMiddleware):
        self.middleware = middleware
    
    async def get_current_user(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[Dict[str, Any]]:
        """Dependency to get current user"""
        return await self.middleware.get_current_user(credentials)
    
    def require_auth(self):
        """Dependency that requires authentication"""
        async def dependency(current_user: Optional[Dict[str, Any]] = Depends(self.get_current_user)):
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            return current_user
        return dependency
    
    def require_permission(self, permission: str, branch: Optional[str] = None):
        """Dependency that requires specific permission"""
        async def dependency(current_user: Dict[str, Any] = Depends(self.require_auth())):
            has_permission = await self.middleware.check_permission(current_user, permission, branch)
            if not has_permission:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Permission {permission} required"
                )
            return current_user
        return dependency
    
    def require_branch_access(self, branch: str):
        """Dependency that requires access to specific branch"""
        async def dependency(current_user: Dict[str, Any] = Depends(self.require_auth())):
            rbac_context = current_user.get('rbac_context')
            if not rbac_context:
                raise HTTPException(status_code=403, detail="No RBAC context")
            
            accessible_branches = rbac_context.get_accessible_branches()
            
            # System admin has access to all branches
            is_system_admin = any(
                ur.role and ur.role.name == SystemRole.SYSTEM_ADMIN.value and ur.is_valid()
                for ur in rbac_context.user_roles
            )
            
            if not is_system_admin and branch not in accessible_branches:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied to branch: {branch}"
                )
            
            return current_user
        return dependency

def create_rbac_middleware(database: VolunteerDatabase) -> tuple[RBACMiddleware, RBACDependency]:
    """Factory function to create RBAC middleware and dependencies"""
    middleware = RBACMiddleware(database)
    dependency = RBACDependency(middleware)
    return middleware, dependency

# Utility functions for common permission checks
class PermissionChecker:
    """Utility class for permission checking"""
    
    @staticmethod
    def can_manage_users(user_permissions: set, branch: Optional[str] = None) -> bool:
        """Check if user can manage users in branch"""
        if 'users.manage.global' in user_permissions:
            return True
        return branch and f'users.manage.branch' in user_permissions
    
    @staticmethod
    def can_view_analytics(user_permissions: set, branch: Optional[str] = None) -> bool:
        """Check if user can view analytics"""
        if 'analytics.read.global' in user_permissions:
            return True
        if 'analytics.read.branch' in user_permissions and branch:
            return True
        return 'analytics.read.own' in user_permissions
    
    @staticmethod
    def can_manage_volunteers(user_permissions: set, branch: Optional[str] = None) -> bool:
        """Check if user can manage volunteers"""
        if 'volunteers.manage.global' in user_permissions:
            return True
        return branch and 'volunteers.manage.branch' in user_permissions
    
    @staticmethod
    def get_required_permissions_for_action(resource: str, action: str, scope: str = 'own') -> List[str]:
        """Get required permissions for an action"""
        base_perm = f"{resource}.{action}"
        
        permissions = []
        if scope == 'own':
            permissions.append(f"{base_perm}.own")
        elif scope == 'branch':
            permissions.extend([
                f"{base_perm}.branch",
                f"{base_perm}.own"  # Branch permission implies own
            ])
        elif scope == 'global':
            permissions.extend([
                f"{resource}.manage.global",
                f"{base_perm}.global", 
                f"{base_perm}.branch",
                f"{base_perm}.own"
            ])
        
        return permissions

# Error handlers for RBAC
class RBACException(HTTPException):
    """Custom exception for RBAC errors"""
    
    def __init__(self, detail: str, status_code: int = 403):
        super().__init__(status_code=status_code, detail=detail)

class InsufficientPermissionsException(RBACException):
    """Exception for insufficient permissions"""
    
    def __init__(self, permission: str, branch: Optional[str] = None):
        detail = f"Insufficient permissions: {permission} required"
        if branch:
            detail += f" for branch {branch}"
        super().__init__(detail=detail)

class BranchAccessDeniedException(RBACException):
    """Exception for branch access denial"""
    
    def __init__(self, branch: str):
        super().__init__(detail=f"Access denied to branch: {branch}")

# Audit logging
class AuditLogger:
    """Utility for audit logging"""
    
    def __init__(self, rbac_service: RBACService):
        self.rbac_service = rbac_service
    
    async def log_permission_check(self, user_id: str, permission: str, 
                                  branch: Optional[str], granted: bool, 
                                  context: str = None):
        """Log permission check"""
        await self.rbac_service.log_access(
            resource=permission.split('.')[0] if '.' in permission else 'unknown',
            action=permission.split('.')[1] if '.' in permission else 'check',
            user_id=user_id,
            branch=branch,
            granted=granted,
            reason=f"Permission check: {permission}" + (f" ({context})" if context else "")
        )
    
    async def log_role_assignment(self, user_id: str, role_name: str, 
                                 branch: Optional[str], granted_by: str):
        """Log role assignment"""
        await self.rbac_service.log_access(
            resource="rbac",
            action="assign_role",
            user_id=user_id,
            branch=branch,
            resource_id=role_name,
            granted=True,
            reason=f"Role {role_name} assigned by {granted_by}"
        )
    
    async def log_permission_override(self, user_id: str, permission: str, 
                                     branch: Optional[str], granted: bool, 
                                     granted_by: str, reason: str = None):
        """Log permission override"""
        await self.rbac_service.log_access(
            resource="rbac",
            action="override_permission",
            user_id=user_id,
            branch=branch,
            resource_id=permission,
            granted=granted,
            reason=f"Permission override by {granted_by}: {reason or 'No reason provided'}"
        )