"""
Branch-Scoped RBAC Models for Volunteer PathFinder
Implements role-based access control with least-privilege defaults
"""
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

class ResourceType(str, Enum):
    USERS = "users"
    VOLUNTEERS = "volunteers" 
    PROJECTS = "projects"
    ANALYTICS = "analytics"
    RBAC = "rbac"
    SYSTEM = "system"

class ActionType(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"
    EXPORT = "export"

class SystemRole(str, Enum):
    GUEST = "guest"
    VOLUNTEER = "volunteer"
    STAFF = "staff"
    VOLUNTEER_COORDINATOR = "volunteer_coordinator"
    BRANCH_ADMIN = "branch_admin"
    SYSTEM_ADMIN = "system_admin"

class Permission(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., description="Unique permission identifier")
    resource: ResourceType
    action: ActionType
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __str__(self) -> str:
        return f"{self.resource.value}.{self.action.value}"
    
    @classmethod
    def from_name(cls, name: str) -> 'Permission':
        """Create permission from name like 'users.read.branch'"""
        parts = name.split('.')
        if len(parts) < 2:
            raise ValueError(f"Invalid permission name: {name}")
        
        resource = ResourceType(parts[0])
        action = ActionType(parts[1])
        return cls(name=name, resource=resource, action=action)

class Role(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., description="Unique role name")
    description: Optional[str] = None
    is_system_role: bool = False
    permissions: List[Permission] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def has_permission(self, permission: Union[str, Permission]) -> bool:
        """Check if role has a specific permission"""
        perm_name = permission if isinstance(permission, str) else permission.name
        return any(p.name == perm_name for p in self.permissions)
    
    def add_permission(self, permission: Permission) -> None:
        """Add permission to role if not already present"""
        if not self.has_permission(permission):
            self.permissions.append(permission)
    
    def remove_permission(self, permission: Union[str, Permission]) -> bool:
        """Remove permission from role"""
        perm_name = permission if isinstance(permission, str) else permission.name
        original_len = len(self.permissions)
        self.permissions = [p for p in self.permissions if p.name != perm_name]
        return len(self.permissions) < original_len

class UserBranchRole(BaseModel):
    id: Optional[str] = None
    user_id: str
    role_id: str
    role: Optional[Role] = None
    branch: Optional[str] = None  # None means global access
    granted_by: Optional[str] = None
    granted_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if role assignment is expired"""
        return self.expires_at is not None and self.expires_at <= datetime.now()
    
    def is_valid(self) -> bool:
        """Check if role assignment is valid (active and not expired)"""
        return self.is_active and not self.is_expired()

class PermissionOverride(BaseModel):
    id: Optional[str] = None
    user_id: str
    permission_id: str
    permission: Optional[Permission] = None
    branch: Optional[str] = None  # None means global override
    granted: bool  # True = grant, False = deny
    granted_by: Optional[str] = None
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if override is expired"""
        return self.expires_at is not None and self.expires_at <= datetime.now()
    
    def is_valid(self) -> bool:
        """Check if override is valid (not expired)"""
        return not self.is_expired()

class AccessLogEntry(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    resource: ResourceType
    action: ActionType
    branch: Optional[str] = None
    resource_id: Optional[str] = None
    granted: bool
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class RBACContext(BaseModel):
    """Context for RBAC operations"""
    user_id: str
    user_roles: List[UserBranchRole] = Field(default_factory=list)
    permission_overrides: List[PermissionOverride] = Field(default_factory=list)
    current_branch: Optional[str] = None
    
    def get_user_permissions(self, branch: Optional[str] = None) -> Set[str]:
        """Get all permissions for user in specified branch"""
        permissions = set()
        target_branch = branch or self.current_branch
        
        # Get permissions from roles
        for user_role in self.user_roles:
            if not user_role.is_valid():
                continue
            
            # Check if role applies to target branch
            if user_role.branch is None or user_role.branch == target_branch:
                if user_role.role:
                    permissions.update(p.name for p in user_role.role.permissions)
        
        # Apply permission overrides
        for override in self.permission_overrides:
            if not override.is_valid():
                continue
            
            # Check if override applies to target branch
            if override.branch is None or override.branch == target_branch:
                if override.permission:
                    if override.granted:
                        permissions.add(override.permission.name)
                    else:
                        permissions.discard(override.permission.name)
        
        return permissions
    
    def has_permission(self, permission: str, branch: Optional[str] = None) -> bool:
        """Check if user has specific permission in branch"""
        user_permissions = self.get_user_permissions(branch)
        return permission in user_permissions
    
    def get_accessible_branches(self) -> Set[str]:
        """Get all branches user has any access to"""
        branches = set()
        for user_role in self.user_roles:
            if user_role.is_valid() and user_role.branch:
                branches.add(user_role.branch)
        return branches

class RBACService:
    """Service class for RBAC operations"""
    
    def __init__(self, database):
        self.database = database
        self._permission_cache: Dict[str, Permission] = {}
        self._role_cache: Dict[str, Role] = {}
        
    def get_least_privilege_defaults(self) -> Dict[SystemRole, List[str]]:
        """Get least-privilege default permissions for each role"""
        return {
            SystemRole.GUEST: [
                "projects.read.public"
            ],
            SystemRole.VOLUNTEER: [
                "users.read.own",
                "users.update.own", 
                "volunteers.read.own",
                "volunteers.update.own",
                "projects.read.public",
                "analytics.read.own",
                "rbac.read.own"
            ],
            SystemRole.STAFF: [
                "users.read.own",
                "users.update.own",
                "volunteers.read.own", 
                "volunteers.update.own",
                "volunteers.read.branch",
                "projects.read.public",
                "projects.read.branch",
                "analytics.read.own",
                "analytics.read.branch",
                "rbac.read.own",
                "rbac.read.branch"
            ],
            SystemRole.VOLUNTEER_COORDINATOR: [
                "users.read.own",
                "users.update.own",
                "users.read.branch",
                "volunteers.read.own",
                "volunteers.update.own", 
                "volunteers.read.branch",
                "volunteers.manage.branch",
                "projects.read.public",
                "projects.read.branch",
                "projects.update.branch",
                "analytics.read.own",
                "analytics.read.branch",
                "rbac.read.own",
                "rbac.read.branch"
            ],
            SystemRole.BRANCH_ADMIN: [
                "users.read.own",
                "users.update.own",
                "users.read.branch",
                "users.create.branch", 
                "users.update.branch",
                "volunteers.read.own",
                "volunteers.update.own",
                "volunteers.manage.branch",
                "projects.read.public",
                "projects.read.branch",
                "projects.create.branch",
                "projects.update.branch",
                "projects.delete.branch",
                "analytics.read.own",
                "analytics.read.branch",
                "analytics.export.branch",
                "rbac.read.own",
                "rbac.read.branch",
                "rbac.manage.branch"
            ],
            SystemRole.SYSTEM_ADMIN: [
                # System admin gets all permissions
                "users.manage.global",
                "volunteers.manage.global", 
                "projects.manage.global",
                "analytics.read.global",
                "analytics.export.global",
                "rbac.manage.global",
                "system.read",
                "system.manage"
            ]
        }
    
    async def create_role(self, name: str, description: str = None, 
                         permissions: List[str] = None) -> Role:
        """Create a new role with specified permissions"""
        try:
            role_data = {
                'name': name,
                'description': description or f'Custom role: {name}',
                'is_system_role': False
            }
            
            # Insert role into database
            result = await self.database.supabase.table('roles').insert(role_data).execute()
            if not result.data:
                raise Exception("Failed to create role")
            
            role_dict = result.data[0]
            role = Role(**role_dict)
            
            # Add permissions if specified
            if permissions:
                await self.add_permissions_to_role(role.id, permissions)
                # Reload role with permissions
                role = await self.get_role_by_id(role.id)
            
            return role
            
        except Exception as e:
            logger.error(f"Error creating role {name}: {e}")
            raise
    
    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID with permissions"""
        try:
            # Get role
            result = await self.database.supabase.table('roles')\
                .select('*')\
                .eq('id', role_id)\
                .execute()
            
            if not result.data:
                return None
            
            role_data = result.data[0]
            
            # Get role permissions
            perms_result = await self.database.supabase.table('role_permissions')\
                .select('*, permissions(*)')\
                .eq('role_id', role_id)\
                .execute()
            
            permissions = []
            for perm_data in perms_result.data:
                if perm_data.get('permissions'):
                    permissions.append(Permission(**perm_data['permissions']))
            
            role = Role(**role_data, permissions=permissions)
            return role
            
        except Exception as e:
            logger.error(f"Error getting role {role_id}: {e}")
            return None
    
    async def assign_role_to_user(self, user_id: str, role_id: str, 
                                 branch: Optional[str] = None,
                                 granted_by: Optional[str] = None,
                                 expires_at: Optional[datetime] = None) -> bool:
        """Assign role to user for specific branch"""
        try:
            assignment_data = {
                'user_id': user_id,
                'role_id': role_id,
                'branch': branch,
                'granted_by': granted_by,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'is_active': True
            }
            
            result = await self.database.supabase.table('user_branch_roles')\
                .insert(assignment_data)\
                .execute()
            
            success = len(result.data) > 0
            
            if success:
                logger.info(f"Assigned role {role_id} to user {user_id} for branch {branch}")
                # Log the assignment
                await self.log_access("rbac", "create", user_id, branch, 
                                    resource_id=f"role:{role_id}", granted=True,
                                    reason="Role assignment")
            
            return success
            
        except Exception as e:
            logger.error(f"Error assigning role to user: {e}")
            return False
    
    async def get_user_context(self, user_id: str) -> RBACContext:
        """Get full RBAC context for user"""
        try:
            # Get user roles with role details
            roles_result = await self.database.supabase.table('user_branch_roles')\
                .select('*, roles(*, role_permissions(*, permissions(*)))')\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .execute()
            
            user_roles = []
            for role_data in roles_result.data:
                # Build role with permissions
                role_info = role_data.get('roles', {})
                permissions = []
                
                for rp in role_info.get('role_permissions', []):
                    if rp.get('permissions'):
                        permissions.append(Permission(**rp['permissions']))
                
                role = Role(**role_info, permissions=permissions) if role_info else None
                
                user_role = UserBranchRole(**role_data, role=role)
                if user_role.is_valid():
                    user_roles.append(user_role)
            
            # Get permission overrides
            overrides_result = await self.database.supabase.table('user_permission_overrides')\
                .select('*, permissions(*)')\
                .eq('user_id', user_id)\
                .execute()
            
            overrides = []
            for override_data in overrides_result.data:
                permission = None
                if override_data.get('permissions'):
                    permission = Permission(**override_data['permissions'])
                
                override = PermissionOverride(**override_data, permission=permission)
                if override.is_valid():
                    overrides.append(override)
            
            return RBACContext(
                user_id=user_id,
                user_roles=user_roles,
                permission_overrides=overrides
            )
            
        except Exception as e:
            logger.error(f"Error getting user context for {user_id}: {e}")
            return RBACContext(user_id=user_id)
    
    async def check_permission(self, user_id: str, permission: str, 
                              branch: Optional[str] = None) -> bool:
        """Check if user has permission in branch"""
        try:
            context = await self.get_user_context(user_id)
            has_perm = context.has_permission(permission, branch)
            
            # Log access attempt
            await self.log_access(
                resource=permission.split('.')[0] if '.' in permission else 'unknown',
                action=permission.split('.')[1] if '.' in permission else 'unknown',
                user_id=user_id,
                branch=branch,
                granted=has_perm,
                reason=f"Permission check: {permission}"
            )
            
            return has_perm
            
        except Exception as e:
            logger.error(f"Error checking permission {permission} for user {user_id}: {e}")
            return False
    
    async def log_access(self, resource: str, action: str, user_id: str = None,
                        branch: str = None, resource_id: str = None,
                        granted: bool = False, reason: str = None) -> bool:
        """Log access attempt"""
        try:
            log_data = {
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'branch': branch,
                'resource_id': resource_id,
                'granted': granted,
                'reason': reason
            }
            
            result = await self.database.supabase.table('access_logs')\
                .insert(log_data)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error logging access: {e}")
            return False
    
    async def bootstrap_system_roles(self) -> bool:
        """Bootstrap system with default roles and permissions"""
        try:
            defaults = self.get_least_privilege_defaults()
            
            for role_name, permissions in defaults.items():
                # Check if role exists
                result = await self.database.supabase.table('roles')\
                    .select('id')\
                    .eq('name', role_name.value)\
                    .execute()
                
                if not result.data:
                    logger.info(f"Creating system role: {role_name.value}")
                    await self.create_role(
                        name=role_name.value,
                        description=f"System role: {role_name.value}",
                        permissions=permissions
                    )
                else:
                    logger.info(f"System role {role_name.value} already exists")
            
            logger.info("System roles bootstrap completed")
            return True
            
        except Exception as e:
            logger.error(f"Error bootstrapping system roles: {e}")
            return False
    
    async def add_permissions_to_role(self, role_id: str, permissions: List[str]) -> bool:
        """Add permissions to role"""
        try:
            # Get permission IDs
            perm_result = await self.database.supabase.table('permissions')\
                .select('id, name')\
                .in_('name', permissions)\
                .execute()
            
            perm_mappings = []
            for perm in perm_result.data:
                perm_mappings.append({
                    'role_id': role_id,
                    'permission_id': perm['id']
                })
            
            if perm_mappings:
                await self.database.supabase.table('role_permissions')\
                    .insert(perm_mappings)\
                    .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding permissions to role: {e}")
            return False