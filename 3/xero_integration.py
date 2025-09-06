"""
Xero Integration for Volunteer Reimbursement & Stipend Tracking
Handles authentication, bill creation, and expense synchronization
"""
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from config import settings
import base64

logger = logging.getLogger(__name__)

class XeroIntegration:
    """Xero API integration for volunteer expense management"""
    
    def __init__(self, access_token: str = None, refresh_token: str = None, tenant_id: str = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.tenant_id = tenant_id
        self.base_url = "https://api.xero.com/api.xro/2.0"
        self.oauth_url = "https://identity.xero.com/connect/token"
        
    def get_auth_url(self, state: str = None) -> str:
        """Generate Xero OAuth authorization URL"""
        params = {
            'response_type': 'code',
            'client_id': settings.XERO_CLIENT_ID,
            'redirect_uri': settings.XERO_REDIRECT_URI,
            'scope': 'accounting.transactions accounting.contacts accounting.settings',
            'state': state or 'default'
        }
        
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"https://login.xero.com/identity/connect/authorize?{param_string}"
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        try:
            # Create basic auth header
            credentials = f"{settings.XERO_CLIENT_ID}:{settings.XERO_CLIENT_SECRET}"
            auth_header = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'authorization_code',
                'client_id': settings.XERO_CLIENT_ID,
                'code': authorization_code,
                'redirect_uri': settings.XERO_REDIRECT_URI
            }
            
            response = requests.post(
                self.oauth_url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                return token_data
            else:
                logger.error(f"Xero token exchange failed: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error exchanging Xero authorization code: {e}")
            return {}
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        try:
            credentials = f"{settings.XERO_CLIENT_ID}:{settings.XERO_CLIENT_SECRET}"
            auth_header = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
            
            response = requests.post(
                self.oauth_url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                if 'refresh_token' in token_data:
                    self.refresh_token = token_data['refresh_token']
                return True
            else:
                logger.error(f"Xero token refresh failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing Xero token: {e}")
            return False
    
    def get_tenants(self) -> List[Dict]:
        """Get list of available tenants"""
        if not self.access_token:
            return []
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                "https://api.xero.com/connections",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get Xero tenants: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting Xero tenants: {e}")
            return []
    
    def _make_api_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make authenticated API request to Xero"""
        if not self.access_token or not self.tenant_id:
            logger.error("Xero access token or tenant ID not available")
            return None
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Xero-tenant-id': self.tenant_id,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.status_code == 401:
                # Try refreshing token once
                if self.refresh_access_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    if method.upper() == 'GET':
                        response = requests.get(url, headers=headers, timeout=30)
                    elif method.upper() == 'POST':
                        response = requests.post(url, headers=headers, json=data, timeout=30)
                    elif method.upper() == 'PUT':
                        response = requests.put(url, headers=headers, json=data, timeout=30)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Xero API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Xero API request error: {e}")
            return None
    
    def get_organisation(self) -> Optional[Dict]:
        """Get organisation information"""
        result = self._make_api_request('GET', 'Organisation')
        if result and 'Organisations' in result:
            return result['Organisations'][0] if result['Organisations'] else None
        return None
    
    def get_chart_of_accounts(self) -> List[Dict]:
        """Get chart of accounts"""
        result = self._make_api_request('GET', 'Accounts')
        if result and 'Accounts' in result:
            return result['Accounts']
        return []
    
    def get_contacts(self, contact_type: str = None) -> List[Dict]:
        """Get list of contacts (suppliers/customers)"""
        endpoint = 'Contacts'
        if contact_type:
            endpoint += f"?where=IsSupplier=={contact_type.lower() == 'supplier'}"
            
        result = self._make_api_request('GET', endpoint)
        if result and 'Contacts' in result:
            return result['Contacts']
        return []
    
    def create_contact(self, volunteer_data: Dict) -> Optional[Dict]:
        """Create a supplier contact for a volunteer"""
        contact_data = {
            "Contacts": [{
                "Name": f"{volunteer_data.get('first_name', '')} {volunteer_data.get('last_name', '')}".strip(),
                "IsSupplier": True,
                "IsCustomer": False,
                "ContactStatus": "ACTIVE"
            }]
        }
        
        # Add contact information if available
        contact_info = contact_data["Contacts"][0]
        
        if volunteer_data.get('email'):
            contact_info["EmailAddress"] = volunteer_data['email']
        
        if any(volunteer_data.get(field) for field in ['city', 'state', 'zip_code']):
            address = {
                "AddressType": "POBOX",
                "City": volunteer_data.get('city', ''),
                "Region": volunteer_data.get('state', ''),
                "PostalCode": volunteer_data.get('zip_code', ''),
                "Country": volunteer_data.get('country', 'US')
            }
            contact_info["Addresses"] = [address]
        
        if volunteer_data.get('phone'):
            contact_info["Phones"] = [{
                "PhoneType": "DEFAULT",
                "PhoneNumber": volunteer_data['phone']
            }]
        
        result = self._make_api_request('POST', 'Contacts', contact_data)
        if result and 'Contacts' in result:
            return result['Contacts'][0] if result['Contacts'] else None
        return None
    
    def create_bill(self, contact_id: str, line_items: List[Dict], due_date: str = None, reference: str = None) -> Optional[Dict]:
        """Create a bill for volunteer reimbursement"""
        bill_data = {
            "Bills": [{
                "Type": "ACCPAY",
                "Contact": {"ContactID": contact_id},
                "Date": datetime.now().strftime('%Y-%m-%d'),
                "Status": "AUTHORISED",
                "LineItems": []
            }]
        }
        
        if due_date:
            bill_data["Bills"][0]["DueDate"] = due_date
        
        if reference:
            bill_data["Bills"][0]["Reference"] = reference
        
        # Add line items
        for item in line_items:
            line = {
                "Description": item.get('description', 'Volunteer expense'),
                "Quantity": 1,
                "UnitAmount": item['amount'],
                "AccountCode": item.get('account_code', settings.XERO_DEFAULT_EXPENSE_ACCOUNT)
            }
            bill_data["Bills"][0]["LineItems"].append(line)
        
        result = self._make_api_request('POST', 'Bills', bill_data)
        if result and 'Bills' in result:
            return result['Bills'][0] if result['Bills'] else None
        return None
    
    def create_expense_claim(self, user_id: str, line_items: List[Dict], status: str = "SUBMITTED") -> Optional[Dict]:
        """Create an expense claim for volunteer reimbursement"""
        expense_data = {
            "ExpenseClaims": [{
                "UserID": user_id,
                "Status": status,
                "Receipts": []
            }]
        }
        
        # Add receipt items
        for item in line_items:
            receipt = {
                "Date": item.get('date', datetime.now().strftime('%Y-%m-%d')),
                "Contact": {"Name": "YMCA Volunteer Expenses"},
                "Total": item['amount'],
                "LineItems": [{
                    "Description": item.get('description', 'Volunteer expense'),
                    "UnitAmount": item['amount'],
                    "Quantity": 1,
                    "AccountCode": item.get('account_code', settings.XERO_DEFAULT_EXPENSE_ACCOUNT)
                }]
            }
            expense_data["ExpenseClaims"][0]["Receipts"].append(receipt)
        
        result = self._make_api_request('POST', 'ExpenseClaims', expense_data)
        if result and 'ExpenseClaims' in result:
            return result['ExpenseClaims'][0] if result['ExpenseClaims'] else None
        return None
    
    def get_bill(self, bill_id: str) -> Optional[Dict]:
        """Get bill details"""
        result = self._make_api_request('GET', f'Bills/{bill_id}')
        if result and 'Bills' in result:
            return result['Bills'][0] if result['Bills'] else None
        return None
    
    def update_bill(self, bill_id: str, bill_data: Dict) -> Optional[Dict]:
        """Update an existing bill"""
        result = self._make_api_request('PUT', f'Bills/{bill_id}', bill_data)
        if result and 'Bills' in result:
            return result['Bills'][0] if result['Bills'] else None
        return None
    
    def sync_volunteer_expenses(self, volunteer_data: Dict, expenses: List[Dict]) -> Dict[str, Any]:
        """Sync volunteer expenses to Xero"""
        try:
            # Find or create contact for volunteer
            contacts = self.get_contacts('supplier')
            volunteer_name = f"{volunteer_data.get('first_name', '')} {volunteer_data.get('last_name', '')}".strip()
            
            contact = None
            for c in contacts:
                if c.get('Name') == volunteer_name:
                    contact = c
                    break
            
            if not contact:
                contact = self.create_contact(volunteer_data)
                if not contact:
                    return {"success": False, "error": "Failed to create contact"}
            
            contact_id = contact['ContactID']
            
            # Create bill with expenses
            line_items = []
            for expense in expenses:
                line_items.append({
                    'amount': expense['amount'],
                    'description': expense['description'],
                    'account_code': expense.get('xero_account_code', settings.XERO_DEFAULT_EXPENSE_ACCOUNT)
                })
            
            bill = self.create_bill(
                contact_id=contact_id,
                line_items=line_items,
                reference=f"Volunteer-{datetime.now().strftime('%Y%m%d')}"
            )
            
            if bill:
                return {
                    "success": True,
                    "bill_id": bill['BillID'],
                    "contact_id": contact_id,
                    "total_amount": bill.get('Total', 0)
                }
            else:
                return {"success": False, "error": "Failed to create bill"}
                
        except Exception as e:
            logger.error(f"Error syncing volunteer expenses to Xero: {e}")
            return {"success": False, "error": str(e)}