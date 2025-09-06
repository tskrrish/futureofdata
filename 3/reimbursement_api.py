"""
FastAPI endpoints for Volunteer Reimbursement & Stipend Tracking
Integrates with existing YMCA Volunteer PathFinder system
"""
from fastapi import HTTPException, BackgroundTasks, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import uuid
import logging
import os

from reimbursement_manager import ReimbursementManager, ExpenseItem, StipendItem
from quickbooks_integration import QuickBooksIntegration
from xero_integration import XeroIntegration

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class ExpenseSubmission(BaseModel):
    project_id: Optional[int] = None
    category_id: str
    description: str
    amount: float
    expense_date: date
    receipt_filename: Optional[str] = None

class StipendSubmission(BaseModel):
    project_id: Optional[int] = None
    stipend_type: str  # 'hourly', 'fixed', 'event_based'
    amount: float
    hours_worked: Optional[float] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    description: Optional[str] = None

class ExpenseApproval(BaseModel):
    expense_id: str
    approved: bool
    notes: Optional[str] = None

class StipendApproval(BaseModel):
    stipend_id: str
    approved: bool
    notes: Optional[str] = None

class BatchCreation(BaseModel):
    expense_ids: List[str]

class AccountingIntegrationSetup(BaseModel):
    platform: str  # 'quickbooks' or 'xero'
    access_token: str
    refresh_token: Optional[str] = None
    company_id: Optional[str] = None
    tenant_id: Optional[str] = None
    organization_id: str = "default"

class BatchProcessing(BaseModel):
    platform: str = "quickbooks"

def setup_reimbursement_api(app, database, reimbursement_manager: ReimbursementManager):
    """Set up reimbursement API endpoints"""
    
    # Expense management endpoints
    @app.post("/api/expenses/submit")
    async def submit_expense(
        expense_data: ExpenseSubmission,
        user_id: str = None,
        background_tasks: BackgroundTasks = None
    ) -> JSONResponse:
        """Submit a new volunteer expense for reimbursement"""
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID required")
        
        try:
            expense = ExpenseItem(
                user_id=user_id,
                project_id=expense_data.project_id,
                category_id=expense_data.category_id,
                description=expense_data.description,
                amount=expense_data.amount,
                expense_date=expense_data.expense_date.isoformat(),
                receipt_filename=expense_data.receipt_filename
            )
            
            expense_id = await reimbursement_manager.submit_expense(expense)
            
            if expense_id:
                return JSONResponse(content={
                    "success": True,
                    "expense_id": expense_id,
                    "message": "Expense submitted successfully"
                })
            else:
                raise HTTPException(status_code=500, detail="Failed to submit expense")
                
        except Exception as e:
            logger.error(f"Error submitting expense: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit expense")
    
    @app.post("/api/expenses/upload-receipt/{expense_id}")
    async def upload_receipt(
        expense_id: str,
        file: UploadFile = File(...),
        user_id: str = None
    ) -> JSONResponse:
        """Upload receipt for an expense"""
        
        try:
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
            if file.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Invalid file type")
            
            # Create upload directory
            upload_dir = "uploads/receipts"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            unique_filename = f"{expense_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Update expense with receipt information
            if database._is_available():
                update_data = {
                    'receipt_url': file_path,
                    'receipt_filename': file.filename,
                    'updated_at': datetime.now().isoformat()
                }
                
                result = database.supabase.table('volunteer_expenses')\
                    .update(update_data)\
                    .eq('id', expense_id)\
                    .eq('user_id', user_id)\
                    .execute()
                
                if result.data:
                    return JSONResponse(content={
                        "success": True,
                        "receipt_url": file_path,
                        "message": "Receipt uploaded successfully"
                    })
            
            raise HTTPException(status_code=500, detail="Failed to update expense record")
            
        except Exception as e:
            logger.error(f"Error uploading receipt: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload receipt")
    
    @app.get("/api/expenses/user/{user_id}")
    async def get_user_expenses(
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> JSONResponse:
        """Get expenses for a specific user"""
        
        try:
            expenses = await reimbursement_manager.get_user_expenses(
                user_id=user_id,
                status=status,
                limit=limit
            )
            
            return JSONResponse(content={
                "success": True,
                "expenses": expenses,
                "total_count": len(expenses)
            })
            
        except Exception as e:
            logger.error(f"Error getting user expenses: {e}")
            raise HTTPException(status_code=500, detail="Failed to get expenses")
    
    @app.post("/api/expenses/approve")
    async def approve_expense(
        approval_data: ExpenseApproval,
        approver_id: str = None,
        background_tasks: BackgroundTasks = None
    ) -> JSONResponse:
        """Approve or reject an expense"""
        
        if not approver_id:
            raise HTTPException(status_code=400, detail="Approver ID required")
        
        try:
            if approval_data.approved:
                success = await reimbursement_manager.approve_expense(
                    expense_id=approval_data.expense_id,
                    approver_id=approver_id,
                    notes=approval_data.notes
                )
            else:
                success = await reimbursement_manager.reject_expense(
                    expense_id=approval_data.expense_id,
                    approver_id=approver_id,
                    notes=approval_data.notes
                )
            
            if success:
                action = "approved" if approval_data.approved else "rejected"
                return JSONResponse(content={
                    "success": True,
                    "message": f"Expense {action} successfully"
                })
            else:
                raise HTTPException(status_code=500, detail="Failed to update expense")
                
        except Exception as e:
            logger.error(f"Error approving/rejecting expense: {e}")
            raise HTTPException(status_code=500, detail="Failed to process approval")
    
    # Stipend management endpoints
    @app.post("/api/stipends/submit")
    async def submit_stipend(
        stipend_data: StipendSubmission,
        user_id: str = None,
        background_tasks: BackgroundTasks = None
    ) -> JSONResponse:
        """Submit a new volunteer stipend"""
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID required")
        
        try:
            stipend = StipendItem(
                user_id=user_id,
                project_id=stipend_data.project_id,
                stipend_type=stipend_data.stipend_type,
                amount=stipend_data.amount,
                hours_worked=stipend_data.hours_worked,
                period_start=stipend_data.period_start.isoformat() if stipend_data.period_start else None,
                period_end=stipend_data.period_end.isoformat() if stipend_data.period_end else None,
                description=stipend_data.description
            )
            
            stipend_id = await reimbursement_manager.submit_stipend(stipend)
            
            if stipend_id:
                return JSONResponse(content={
                    "success": True,
                    "stipend_id": stipend_id,
                    "message": "Stipend submitted successfully"
                })
            else:
                raise HTTPException(status_code=500, detail="Failed to submit stipend")
                
        except Exception as e:
            logger.error(f"Error submitting stipend: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit stipend")
    
    @app.get("/api/stipends/user/{user_id}")
    async def get_user_stipends(
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> JSONResponse:
        """Get stipends for a specific user"""
        
        try:
            stipends = await reimbursement_manager.get_user_stipends(
                user_id=user_id,
                status=status,
                limit=limit
            )
            
            return JSONResponse(content={
                "success": True,
                "stipends": stipends,
                "total_count": len(stipends)
            })
            
        except Exception as e:
            logger.error(f"Error getting user stipends: {e}")
            raise HTTPException(status_code=500, detail="Failed to get stipends")
    
    @app.post("/api/stipends/approve")
    async def approve_stipend(
        approval_data: StipendApproval,
        approver_id: str = None,
        background_tasks: BackgroundTasks = None
    ) -> JSONResponse:
        """Approve or reject a stipend"""
        
        if not approver_id:
            raise HTTPException(status_code=400, detail="Approver ID required")
        
        try:
            # Update stipend status
            status = "approved" if approval_data.approved else "rejected"
            update_data = {
                'status': status,
                'approved_by': approver_id,
                'approved_at': datetime.now().isoformat(),
                'approval_notes': approval_data.notes,
                'updated_at': datetime.now().isoformat()
            }
            
            result = database.supabase.table('volunteer_stipends')\
                .update(update_data)\
                .eq('id', approval_data.stipend_id)\
                .execute()
            
            if result.data:
                action = "approved" if approval_data.approved else "rejected"
                return JSONResponse(content={
                    "success": True,
                    "message": f"Stipend {action} successfully"
                })
            else:
                raise HTTPException(status_code=500, detail="Failed to update stipend")
                
        except Exception as e:
            logger.error(f"Error approving/rejecting stipend: {e}")
            raise HTTPException(status_code=500, detail="Failed to process approval")
    
    # Batch processing endpoints
    @app.post("/api/reimbursements/create-batch")
    async def create_reimbursement_batch(
        batch_data: BatchCreation,
        user_id: str = None,
        creator_id: str = None,
        background_tasks: BackgroundTasks = None
    ) -> JSONResponse:
        """Create a reimbursement batch from approved expenses"""
        
        if not user_id or not creator_id:
            raise HTTPException(status_code=400, detail="User ID and creator ID required")
        
        try:
            batch_id = await reimbursement_manager.create_reimbursement_batch(
                user_id=user_id,
                expense_ids=batch_data.expense_ids,
                created_by=creator_id
            )
            
            if batch_id:
                return JSONResponse(content={
                    "success": True,
                    "batch_id": batch_id,
                    "message": "Reimbursement batch created successfully"
                })
            else:
                raise HTTPException(status_code=500, detail="Failed to create batch")
                
        except Exception as e:
            logger.error(f"Error creating reimbursement batch: {e}")
            raise HTTPException(status_code=500, detail="Failed to create batch")
    
    @app.post("/api/reimbursements/process-batch/{batch_id}")
    async def process_reimbursement_batch(
        batch_id: str,
        processing_data: BatchProcessing,
        background_tasks: BackgroundTasks = None
    ) -> JSONResponse:
        """Process a reimbursement batch through accounting software"""
        
        try:
            result = await reimbursement_manager.process_reimbursement_batch(
                batch_id=batch_id,
                platform=processing_data.platform
            )
            
            if result.get('success'):
                return JSONResponse(content=result)
            else:
                raise HTTPException(status_code=500, detail=result.get('error', 'Processing failed'))
                
        except Exception as e:
            logger.error(f"Error processing reimbursement batch: {e}")
            raise HTTPException(status_code=500, detail="Failed to process batch")
    
    # Admin and reporting endpoints
    @app.get("/api/admin/pending-approvals")
    async def get_pending_approvals(
        limit: int = 100
    ) -> JSONResponse:
        """Get items pending approval (admin only)"""
        
        try:
            pending_items = await reimbursement_manager.get_pending_approvals(limit=limit)
            
            return JSONResponse(content={
                "success": True,
                "pending_expenses": pending_items['expenses'],
                "pending_stipends": pending_items['stipends'],
                "total_expenses": len(pending_items['expenses']),
                "total_stipends": len(pending_items['stipends'])
            })
            
        except Exception as e:
            logger.error(f"Error getting pending approvals: {e}")
            raise HTTPException(status_code=500, detail="Failed to get pending approvals")
    
    @app.get("/api/reports/reimbursement-summary")
    async def get_reimbursement_summary(
        user_id: Optional[str] = None,
        days: int = 30
    ) -> JSONResponse:
        """Get reimbursement summary statistics"""
        
        try:
            summary = await reimbursement_manager.get_reimbursement_summary(
                user_id=user_id,
                days=days
            )
            
            return JSONResponse(content={
                "success": True,
                "summary": summary
            })
            
        except Exception as e:
            logger.error(f"Error getting reimbursement summary: {e}")
            raise HTTPException(status_code=500, detail="Failed to get summary")
    
    @app.get("/api/expense-categories")
    async def get_expense_categories() -> JSONResponse:
        """Get all available expense categories"""
        
        try:
            categories = await reimbursement_manager.get_expense_categories()
            
            return JSONResponse(content={
                "success": True,
                "categories": categories
            })
            
        except Exception as e:
            logger.error(f"Error getting expense categories: {e}")
            raise HTTPException(status_code=500, detail="Failed to get categories")
    
    # Accounting integration endpoints
    @app.post("/api/integration/setup")
    async def setup_accounting_integration(
        integration_data: AccountingIntegrationSetup,
        background_tasks: BackgroundTasks = None
    ) -> JSONResponse:
        """Set up QuickBooks or Xero integration"""
        
        try:
            await reimbursement_manager.set_accounting_integration(
                platform=integration_data.platform,
                integration_config=integration_data.dict()
            )
            
            return JSONResponse(content={
                "success": True,
                "message": f"{integration_data.platform.title()} integration set up successfully"
            })
            
        except Exception as e:
            logger.error(f"Error setting up {integration_data.platform} integration: {e}")
            raise HTTPException(status_code=500, detail="Failed to set up integration")
    
    @app.get("/api/integration/quickbooks/auth-url")
    async def get_quickbooks_auth_url(
        state: Optional[str] = None
    ) -> JSONResponse:
        """Get QuickBooks OAuth authorization URL"""
        
        try:
            qb_integration = QuickBooksIntegration()
            auth_url = qb_integration.get_auth_url(state=state)
            
            return JSONResponse(content={
                "success": True,
                "auth_url": auth_url
            })
            
        except Exception as e:
            logger.error(f"Error generating QuickBooks auth URL: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate auth URL")
    
    @app.get("/api/integration/xero/auth-url")
    async def get_xero_auth_url(
        state: Optional[str] = None
    ) -> JSONResponse:
        """Get Xero OAuth authorization URL"""
        
        try:
            xero_integration = XeroIntegration()
            auth_url = xero_integration.get_auth_url(state=state)
            
            return JSONResponse(content={
                "success": True,
                "auth_url": auth_url
            })
            
        except Exception as e:
            logger.error(f"Error generating Xero auth URL: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate auth URL")
    
    @app.post("/api/integration/quickbooks/callback")
    async def quickbooks_oauth_callback(
        code: str,
        realmId: Optional[str] = None,
        background_tasks: BackgroundTasks = None
    ) -> JSONResponse:
        """Handle QuickBooks OAuth callback"""
        
        try:
            qb_integration = QuickBooksIntegration()
            token_data = qb_integration.exchange_code_for_tokens(code)
            
            if token_data.get('access_token'):
                # Set up integration
                integration_config = {
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data.get('refresh_token'),
                    'company_id': realmId or token_data.get('realmId'),
                    'expires_at': token_data.get('expires_at'),
                    'organization_id': 'default'
                }
                
                await reimbursement_manager.set_accounting_integration(
                    platform='quickbooks',
                    integration_config=integration_config
                )
                
                return JSONResponse(content={
                    "success": True,
                    "message": "QuickBooks integration completed successfully"
                })
            else:
                raise HTTPException(status_code=400, detail="Failed to get access token")
                
        except Exception as e:
            logger.error(f"Error in QuickBooks callback: {e}")
            raise HTTPException(status_code=500, detail="Failed to complete integration")
    
    @app.post("/api/integration/xero/callback")
    async def xero_oauth_callback(
        code: str,
        background_tasks: BackgroundTasks = None
    ) -> JSONResponse:
        """Handle Xero OAuth callback"""
        
        try:
            xero_integration = XeroIntegration()
            token_data = xero_integration.exchange_code_for_tokens(code)
            
            if token_data.get('access_token'):
                # Get tenants
                xero_integration.access_token = token_data['access_token']
                tenants = xero_integration.get_tenants()
                
                if tenants:
                    tenant_id = tenants[0]['tenantId']
                    
                    # Set up integration
                    integration_config = {
                        'access_token': token_data['access_token'],
                        'refresh_token': token_data.get('refresh_token'),
                        'tenant_id': tenant_id,
                        'company_name': tenants[0].get('tenantName', ''),
                        'expires_at': token_data.get('expires_at'),
                        'organization_id': 'default'
                    }
                    
                    await reimbursement_manager.set_accounting_integration(
                        platform='xero',
                        integration_config=integration_config
                    )
                    
                    return JSONResponse(content={
                        "success": True,
                        "message": "Xero integration completed successfully",
                        "tenant_name": tenants[0].get('tenantName', '')
                    })
                else:
                    raise HTTPException(status_code=400, detail="No Xero organizations found")
            else:
                raise HTTPException(status_code=400, detail="Failed to get access token")
                
        except Exception as e:
            logger.error(f"Error in Xero callback: {e}")
            raise HTTPException(status_code=500, detail="Failed to complete integration")
    
    return app