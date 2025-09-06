"""
Volunteer Reimbursement & Stipend Manager
Handles business logic for expense tracking, approval workflows, and accounting integration
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import logging
import os
from dataclasses import dataclass
from enum import Enum

from database import VolunteerDatabase
from quickbooks_integration import QuickBooksIntegration
from xero_integration import XeroIntegration

logger = logging.getLogger(__name__)

class ExpenseStatus(Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    REIMBURSED = "reimbursed"

class StipendStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"

class BatchStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"
    PAID = "paid"

@dataclass
class ExpenseItem:
    user_id: str
    project_id: Optional[int]
    category_id: str
    description: str
    amount: float
    expense_date: str
    receipt_url: Optional[str] = None
    receipt_filename: Optional[str] = None

@dataclass
class StipendItem:
    user_id: str
    project_id: Optional[int]
    stipend_type: str
    amount: float
    hours_worked: Optional[float] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    description: Optional[str] = None

class ReimbursementManager:
    """Manages volunteer reimbursements and stipends with accounting integration"""
    
    def __init__(self, database: VolunteerDatabase):
        self.database = database
        self.quickbooks = None
        self.xero = None
        
    async def set_accounting_integration(self, platform: str, integration_config: Dict):
        """Set up accounting integration (QuickBooks or Xero)"""
        try:
            if platform.lower() == 'quickbooks':
                self.quickbooks = QuickBooksIntegration(
                    access_token=integration_config.get('access_token'),
                    refresh_token=integration_config.get('refresh_token'),
                    company_id=integration_config.get('company_id')
                )
            elif platform.lower() == 'xero':
                self.xero = XeroIntegration(
                    access_token=integration_config.get('access_token'),
                    refresh_token=integration_config.get('refresh_token'),
                    tenant_id=integration_config.get('tenant_id')
                )
            
            # Save integration config to database
            await self._save_integration_config(platform, integration_config)
            
        except Exception as e:
            logger.error(f"Error setting up {platform} integration: {e}")
            raise
    
    async def _save_integration_config(self, platform: str, config: Dict):
        """Save accounting integration configuration"""
        if not self.database._is_available():
            return
            
        try:
            integration_data = {
                'organization_id': config.get('organization_id', 'default'),
                'platform': platform.lower(),
                'access_token': config.get('access_token'),
                'refresh_token': config.get('refresh_token'),
                'token_expires_at': config.get('expires_at'),
                'company_id': config.get('company_id') or config.get('tenant_id'),
                'company_name': config.get('company_name', ''),
                'base_currency': config.get('currency', 'USD'),
                'default_expense_account': config.get('expense_account'),
                'default_liability_account': config.get('liability_account'),
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Check if integration already exists
            existing = self.database.supabase.table('accounting_integrations')\
                .select('*')\
                .eq('platform', platform.lower())\
                .eq('organization_id', config.get('organization_id', 'default'))\
                .execute()
            
            if existing.data:
                # Update existing
                result = self.database.supabase.table('accounting_integrations')\
                    .update(integration_data)\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
            else:
                # Create new
                result = self.database.supabase.table('accounting_integrations')\
                    .insert(integration_data)\
                    .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error saving integration config: {e}")
            return False
    
    async def submit_expense(self, expense: ExpenseItem) -> Optional[str]:
        """Submit a new volunteer expense"""
        if not self.database._is_available():
            logger.warning("Database not available, cannot submit expense")
            return None
            
        try:
            expense_id = str(uuid.uuid4())
            expense_data = {
                'id': expense_id,
                'user_id': expense.user_id,
                'project_id': expense.project_id,
                'category_id': expense.category_id,
                'description': expense.description,
                'amount': expense.amount,
                'expense_date': expense.expense_date,
                'receipt_url': expense.receipt_url,
                'receipt_filename': expense.receipt_filename,
                'status': ExpenseStatus.SUBMITTED.value,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.database.supabase.table('volunteer_expenses')\
                .insert(expense_data)\
                .execute()
            
            if result.data:
                logger.info(f"Expense submitted: {expense_id}")
                
                # Track analytics
                await self.database.track_event(
                    'expense_submitted',
                    {
                        'expense_id': expense_id,
                        'amount': expense.amount,
                        'category_id': expense.category_id
                    },
                    expense.user_id
                )
                
                return expense_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error submitting expense: {e}")
            return None
    
    async def submit_stipend(self, stipend: StipendItem) -> Optional[str]:
        """Submit a new volunteer stipend"""
        if not self.database._is_available():
            logger.warning("Database not available, cannot submit stipend")
            return None
            
        try:
            stipend_id = str(uuid.uuid4())
            stipend_data = {
                'id': stipend_id,
                'user_id': stipend.user_id,
                'project_id': stipend.project_id,
                'stipend_type': stipend.stipend_type,
                'amount': stipend.amount,
                'hours_worked': stipend.hours_worked,
                'period_start': stipend.period_start,
                'period_end': stipend.period_end,
                'description': stipend.description,
                'status': StipendStatus.PENDING.value,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.database.supabase.table('volunteer_stipends')\
                .insert(stipend_data)\
                .execute()
            
            if result.data:
                logger.info(f"Stipend submitted: {stipend_id}")
                
                # Track analytics
                await self.database.track_event(
                    'stipend_submitted',
                    {
                        'stipend_id': stipend_id,
                        'amount': stipend.amount,
                        'type': stipend.stipend_type
                    },
                    stipend.user_id
                )
                
                return stipend_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error submitting stipend: {e}")
            return None
    
    async def approve_expense(self, expense_id: str, approver_id: str, notes: str = None) -> bool:
        """Approve a volunteer expense"""
        try:
            update_data = {
                'status': ExpenseStatus.APPROVED.value,
                'approved_by': approver_id,
                'approved_at': datetime.now().isoformat(),
                'approval_notes': notes,
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.database.supabase.table('volunteer_expenses')\
                .update(update_data)\
                .eq('id', expense_id)\
                .execute()
            
            if result.data:
                # Track analytics
                await self.database.track_event(
                    'expense_approved',
                    {
                        'expense_id': expense_id,
                        'approver_id': approver_id
                    },
                    None
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error approving expense: {e}")
            return False
    
    async def reject_expense(self, expense_id: str, approver_id: str, notes: str = None) -> bool:
        """Reject a volunteer expense"""
        try:
            update_data = {
                'status': ExpenseStatus.REJECTED.value,
                'approved_by': approver_id,
                'approved_at': datetime.now().isoformat(),
                'approval_notes': notes,
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.database.supabase.table('volunteer_expenses')\
                .update(update_data)\
                .eq('id', expense_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error rejecting expense: {e}")
            return False
    
    async def create_reimbursement_batch(self, user_id: str, expense_ids: List[str], 
                                       created_by: str) -> Optional[str]:
        """Create a reimbursement batch from approved expenses"""
        try:
            # Get approved expenses
            expenses_query = self.database.supabase.table('volunteer_expenses')\
                .select('*')\
                .in_('id', expense_ids)\
                .eq('status', ExpenseStatus.APPROVED.value)
            
            expenses_result = expenses_query.execute()
            if not expenses_result.data:
                logger.error("No approved expenses found for batch")
                return None
            
            # Calculate total amount
            total_amount = sum(expense['amount'] for expense in expenses_result.data)
            
            # Create batch
            batch_id = str(uuid.uuid4())
            batch_number = f"BATCH-{datetime.now().strftime('%Y%m%d')}-{batch_id[:8]}"
            
            batch_data = {
                'id': batch_id,
                'user_id': user_id,
                'batch_number': batch_number,
                'total_amount': total_amount,
                'status': BatchStatus.PENDING.value,
                'created_by': created_by,
                'created_at': datetime.now().isoformat()
            }
            
            batch_result = self.database.supabase.table('reimbursement_batches')\
                .insert(batch_data)\
                .execute()
            
            if batch_result.data:
                # Link expenses to batch
                batch_expense_data = [
                    {
                        'batch_id': batch_id,
                        'expense_id': expense_id,
                        'created_at': datetime.now().isoformat()
                    }
                    for expense_id in expense_ids
                ]
                
                self.database.supabase.table('batch_expenses')\
                    .insert(batch_expense_data)\
                    .execute()
                
                logger.info(f"Reimbursement batch created: {batch_id}")
                return batch_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating reimbursement batch: {e}")
            return None
    
    async def process_reimbursement_batch(self, batch_id: str, platform: str = 'quickbooks') -> Dict[str, Any]:
        """Process a reimbursement batch through accounting software"""
        try:
            # Get batch and associated expenses
            batch_result = self.database.supabase.table('reimbursement_batches')\
                .select('*, batch_expenses(*, volunteer_expenses(*))')\
                .eq('id', batch_id)\
                .execute()
            
            if not batch_result.data:
                return {"success": False, "error": "Batch not found"}
            
            batch = batch_result.data[0]
            
            # Get volunteer information
            user_result = await self.database.get_user(user_id=batch['user_id'])
            if not user_result:
                return {"success": False, "error": "User not found"}
            
            # Prepare expenses for accounting software
            expenses = []
            for batch_expense in batch['batch_expenses']:
                expense = batch_expense['volunteer_expenses']
                expenses.append({
                    'amount': expense['amount'],
                    'description': expense['description'],
                    'date': expense['expense_date']
                })
            
            # Sync with accounting software
            if platform.lower() == 'quickbooks' and self.quickbooks:
                sync_result = self.quickbooks.sync_volunteer_expenses(user_result, expenses)
            elif platform.lower() == 'xero' and self.xero:
                sync_result = self.xero.sync_volunteer_expenses(user_result, expenses)
            else:
                return {"success": False, "error": f"No {platform} integration available"}
            
            if sync_result.get('success'):
                # Update batch status
                update_data = {
                    'status': BatchStatus.PROCESSED.value,
                    'processed_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                if platform.lower() == 'quickbooks':
                    update_data['quickbooks_bill_id'] = sync_result.get('bill_id')
                elif platform.lower() == 'xero':
                    update_data['xero_bill_id'] = sync_result.get('bill_id')
                
                self.database.supabase.table('reimbursement_batches')\
                    .update(update_data)\
                    .eq('id', batch_id)\
                    .execute()
                
                # Update expense statuses
                expense_ids = [be['expense_id'] for be in batch['batch_expenses']]
                self.database.supabase.table('volunteer_expenses')\
                    .update({'status': ExpenseStatus.REIMBURSED.value})\
                    .in_('id', expense_ids)\
                    .execute()
                
                # Log sync
                await self._log_sync(platform, 'reimbursement', batch_id, 
                                   sync_result.get('bill_id'), 'success')
                
                return {
                    "success": True,
                    "batch_id": batch_id,
                    "external_id": sync_result.get('bill_id'),
                    "total_amount": sync_result.get('total_amount', batch['total_amount'])
                }
            else:
                await self._log_sync(platform, 'reimbursement', batch_id, 
                                   None, 'failed', sync_result.get('error'))
                return sync_result
                
        except Exception as e:
            logger.error(f"Error processing reimbursement batch: {e}")
            await self._log_sync(platform, 'reimbursement', batch_id, 
                               None, 'failed', str(e))
            return {"success": False, "error": str(e)}
    
    async def _log_sync(self, platform: str, sync_type: str, entity_id: str, 
                       external_id: str = None, status: str = 'pending', 
                       error_message: str = None):
        """Log synchronization attempt"""
        try:
            log_data = {
                'sync_type': sync_type,
                'entity_id': entity_id,
                'external_id': external_id,
                'status': status,
                'error_message': error_message,
                'sync_data': {'platform': platform},
                'created_at': datetime.now().isoformat()
            }
            
            self.database.supabase.table('accounting_sync_log')\
                .insert(log_data)\
                .execute()
                
        except Exception as e:
            logger.error(f"Error logging sync: {e}")
    
    async def get_user_expenses(self, user_id: str, status: str = None, 
                               limit: int = 50) -> List[Dict]:
        """Get expenses for a user"""
        try:
            query = self.database.supabase.table('volunteer_expenses')\
                .select('*, expense_categories(name)')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)
            
            if status:
                query = query.eq('status', status)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting user expenses: {e}")
            return []
    
    async def get_user_stipends(self, user_id: str, status: str = None, 
                               limit: int = 50) -> List[Dict]:
        """Get stipends for a user"""
        try:
            query = self.database.supabase.table('volunteer_stipends')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)
            
            if status:
                query = query.eq('status', status)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting user stipends: {e}")
            return []
    
    async def get_expense_categories(self) -> List[Dict]:
        """Get all expense categories"""
        try:
            result = self.database.supabase.table('expense_categories')\
                .select('*')\
                .order('name')\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting expense categories: {e}")
            return []
    
    async def get_pending_approvals(self, limit: int = 100) -> Dict[str, List]:
        """Get items pending approval"""
        try:
            # Get pending expenses
            expenses_result = self.database.supabase.table('volunteer_expenses')\
                .select('*, users(first_name, last_name, email), expense_categories(name)')\
                .eq('status', ExpenseStatus.SUBMITTED.value)\
                .order('created_at')\
                .limit(limit)\
                .execute()
            
            # Get pending stipends
            stipends_result = self.database.supabase.table('volunteer_stipends')\
                .select('*, users(first_name, last_name, email)')\
                .eq('status', StipendStatus.PENDING.value)\
                .order('created_at')\
                .limit(limit)\
                .execute()
            
            return {
                'expenses': expenses_result.data or [],
                'stipends': stipends_result.data or []
            }
            
        except Exception as e:
            logger.error(f"Error getting pending approvals: {e}")
            return {'expenses': [], 'stipends': []}
    
    async def get_reimbursement_summary(self, user_id: str = None, 
                                      days: int = 30) -> Dict[str, Any]:
        """Get reimbursement summary statistics"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Base queries
            expense_query = self.database.supabase.table('volunteer_expenses')\
                .select('amount, status')\
                .gte('created_at', start_date)
            
            stipend_query = self.database.supabase.table('volunteer_stipends')\
                .select('amount, status')\
                .gte('created_at', start_date)
            
            if user_id:
                expense_query = expense_query.eq('user_id', user_id)
                stipend_query = stipend_query.eq('user_id', user_id)
            
            expenses_result = expense_query.execute()
            stipends_result = stipend_query.execute()
            
            # Calculate summaries
            expenses = expenses_result.data or []
            stipends = stipends_result.data or []
            
            expense_totals = {}
            stipend_totals = {}
            
            for expense in expenses:
                status = expense['status']
                amount = float(expense['amount'])
                expense_totals[status] = expense_totals.get(status, 0) + amount
            
            for stipend in stipends:
                status = stipend['status']
                amount = float(stipend['amount'])
                stipend_totals[status] = stipend_totals.get(status, 0) + amount
            
            return {
                'period_days': days,
                'expenses': {
                    'total_submitted': expense_totals.get('submitted', 0),
                    'total_approved': expense_totals.get('approved', 0),
                    'total_reimbursed': expense_totals.get('reimbursed', 0),
                    'total_rejected': expense_totals.get('rejected', 0)
                },
                'stipends': {
                    'total_pending': stipend_totals.get('pending', 0),
                    'total_approved': stipend_totals.get('approved', 0),
                    'total_paid': stipend_totals.get('paid', 0),
                    'total_rejected': stipend_totals.get('rejected', 0)
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting reimbursement summary: {e}")
            return {}