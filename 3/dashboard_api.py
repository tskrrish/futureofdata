"""
FastAPI API for Dashboard Sharing with Permissions
Handles dashboard creation, sharing, and permission management
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime
import logging

from database import VolunteerDatabase
from config import settings

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="YMCA Dashboard Sharing API",
    description="API for managing shared dashboards with view/edit permissions",
    version="1.0.0"
)

# Security
security = HTTPBearer()
db = VolunteerDatabase()

# Pydantic models
class DashboardCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    dashboard_data: Optional[Dict[str, Any]] = {}
    is_public: Optional[bool] = False

class DashboardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    dashboard_data: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None

class ShareDashboard(BaseModel):
    user_email: EmailStr
    permission_type: str  # 'view' or 'edit'

class DashboardResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    description: Optional[str]
    dashboard_data: Optional[Dict[str, Any]]
    is_public: bool
    permission: Optional[str] = None
    shared_at: Optional[str] = None
    created_at: str
    updated_at: str

class PermissionResponse(BaseModel):
    id: str
    dashboard_id: str
    user_id: str
    permission_type: str
    granted_by: str
    user: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

class AccessLogResponse(BaseModel):
    id: str
    dashboard_id: str
    user_id: str
    action: str
    user: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_at: str

# Dependency to get current user from JWT token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extract user ID from JWT token
    In production, this would validate the JWT token and extract user info
    For now, we'll use a simple approach where the token is the user ID
    """
    try:
        # In a real implementation, you would:
        # 1. Validate the JWT token
        # 2. Extract user information
        # 3. Return the user ID
        
        # For demo purposes, we'll treat the token as the user ID
        token = credentials.credentials
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        return token  # In production, this would be the user_id extracted from JWT
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

# Dashboard endpoints
@app.post("/api/dashboards", response_model=DashboardResponse)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: str = Depends(get_current_user)
):
    """Create a new dashboard"""
    try:
        dashboard = await db.create_dashboard(current_user, dashboard_data.dict())
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create dashboard"
            )
        
        # Log the creation
        await db.log_dashboard_access(dashboard['id'], current_user, 'create')
        
        return DashboardResponse(**dashboard)
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/dashboards", response_model=List[DashboardResponse])
async def get_user_dashboards(current_user: str = Depends(get_current_user)):
    """Get all dashboards accessible to the current user"""
    try:
        dashboards = await db.get_user_dashboards(current_user)
        return [DashboardResponse(**dashboard) for dashboard in dashboards]
    except Exception as e:
        logger.error(f"Error getting user dashboards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get a specific dashboard by ID"""
    try:
        dashboard = await db.get_dashboard(dashboard_id, current_user)
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found or access denied"
            )
        
        # Log the access
        await db.log_dashboard_access(dashboard_id, current_user, 'view')
        
        return DashboardResponse(**dashboard)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.put("/api/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: str,
    updates: DashboardUpdate,
    current_user: str = Depends(get_current_user)
):
    """Update a dashboard"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        success = await db.update_dashboard(dashboard_id, update_data, current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to edit this dashboard"
            )
        
        # Get updated dashboard
        dashboard = await db.get_dashboard(dashboard_id, current_user)
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found"
            )
        
        # Log the edit
        await db.log_dashboard_access(dashboard_id, current_user, 'edit', update_data)
        
        return DashboardResponse(**dashboard)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.delete("/api/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete a dashboard (only owner can delete)"""
    try:
        success = await db.delete_dashboard(dashboard_id, current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only dashboard owner can delete the dashboard"
            )
        
        return {"message": "Dashboard deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Sharing endpoints
@app.post("/api/dashboards/{dashboard_id}/share")
async def share_dashboard(
    dashboard_id: str,
    share_data: ShareDashboard,
    current_user: str = Depends(get_current_user)
):
    """Share a dashboard with another user"""
    try:
        if share_data.permission_type not in ['view', 'edit']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission type must be 'view' or 'edit'"
            )
        
        success = await db.share_dashboard(
            dashboard_id,
            share_data.user_email,
            share_data.permission_type,
            current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to share dashboard. User may not exist or you may not be the owner."
            )
        
        # Log the sharing
        await db.log_dashboard_access(
            dashboard_id, 
            current_user, 
            'share', 
            {"shared_with": share_data.user_email, "permission": share_data.permission_type}
        )
        
        return {"message": f"Dashboard shared with {share_data.user_email}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.delete("/api/dashboards/{dashboard_id}/share/{user_id}")
async def revoke_dashboard_access(
    dashboard_id: str,
    user_id: str,
    current_user: str = Depends(get_current_user)
):
    """Revoke dashboard access from a user"""
    try:
        success = await db.revoke_dashboard_access(dashboard_id, user_id, current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only dashboard owner can revoke access"
            )
        
        return {"message": "Dashboard access revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking dashboard access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/dashboards/{dashboard_id}/permissions", response_model=List[PermissionResponse])
async def get_dashboard_permissions(
    dashboard_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get all permissions for a dashboard (only owner can view)"""
    try:
        permissions = await db.get_dashboard_permissions(dashboard_id, current_user)
        return [PermissionResponse(**perm) for perm in permissions]
    except Exception as e:
        logger.error(f"Error getting dashboard permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/dashboards/{dashboard_id}/logs", response_model=List[AccessLogResponse])
async def get_dashboard_access_logs(
    dashboard_id: str,
    limit: int = 50,
    current_user: str = Depends(get_current_user)
):
    """Get dashboard access logs (only owner can view)"""
    try:
        logs = await db.get_dashboard_access_logs(dashboard_id, current_user, limit)
        return [AccessLogResponse(**log) for log in logs]
    except Exception as e:
        logger.error(f"Error getting dashboard access logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# CORS middleware for frontend integration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "dashboard_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )