"""
QuickBooks Integration for Volunteer Reimbursement & Stipend Tracking
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

class QuickBooksIntegration:
    """QuickBooks Online API integration for volunteer expense management"""
    
    def __init__(self, access_token: str = None, refresh_token: str = None, company_id: str = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.company_id = company_id
        self.base_url = "https://sandbox-quickbooks.api.intuit.com" if settings.DEBUG else "https://quickbooks.api.intuit.com"
        self.discovery_url = "https://appcenter.intuit.com/connect/oauth2"
        
    def get_auth_url(self, state: str = None) -> str:
        """Generate QuickBooks OAuth authorization URL"""
        params = {
            'client_id': settings.QUICKBOOKS_CLIENT_ID,
            'scope': 'com.intuit.quickbooks.accounting',
            'redirect_uri': settings.QUICKBOOKS_REDIRECT_URI,
            'response_type': 'code',
            'access_type': 'offline'
        }
        
        if state:
            params['state'] = state
            
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.discovery_url}?{param_string}"
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        try:
            # Create basic auth header
            credentials = f"{settings.QUICKBOOKS_CLIENT_ID}:{settings.QUICKBOOKS_CLIENT_SECRET}"
            auth_header = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': settings.QUICKBOOKS_REDIRECT_URI
            }
            
            response = requests.post(
                f"{self.discovery_url}",
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                
                # Extract company ID from realmId in response
                if 'realmId' in token_data:
                    self.company_id = token_data['realmId']
                
                return token_data
            else:
                logger.error(f"QuickBooks token exchange failed: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error exchanging QuickBooks authorization code: {e}")
            return {}
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        try:
            credentials = f"{settings.QUICKBOOKS_CLIENT_ID}:{settings.QUICKBOOKS_CLIENT_SECRET}"
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
                f"{self.discovery_url}",
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
                logger.error(f"QuickBooks token refresh failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing QuickBooks token: {e}")
            return False
    
    def _make_api_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make authenticated API request to QuickBooks"""
        if not self.access_token or not self.company_id:
            logger.error("QuickBooks access token or company ID not available")
            return None
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/v3/company/{self.company_id}/{endpoint}"
        
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
                logger.error(f"QuickBooks API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"QuickBooks API request error: {e}")
            return None
    
    def get_company_info(self) -> Optional[Dict]:
        """Get company information"""
        result = self._make_api_request('GET', 'companyinfo/1')
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('CompanyInfo', [{}])[0]
        return None
    
    def get_chart_of_accounts(self) -> List[Dict]:
        """Get chart of accounts"""
        result = self._make_api_request('GET', 'accounts')
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('Account', [])
        return []
    
    def get_vendors(self) -> List[Dict]:
        """Get list of vendors"""
        result = self._make_api_request('GET', 'vendors')
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('Vendor', [])
        return []
    
    def create_vendor(self, volunteer_data: Dict) -> Optional[Dict]:
        """Create a vendor for a volunteer"""
        vendor_data = {
            "Name": f"{volunteer_data.get('first_name', '')} {volunteer_data.get('last_name', '')}".strip(),
            "CompanyName": "YMCA Volunteer",
            "Active": True,
            "Vendor1099": False
        }
        
        # Add contact information if available
        if volunteer_data.get('email'):
            vendor_data["PrimaryEmailAddr"] = {"Address": volunteer_data['email']}
        
        if volunteer_data.get('phone'):
            vendor_data["PrimaryPhone"] = {"FreeFormNumber": volunteer_data['phone']}
        
        # Add address if available
        if any(volunteer_data.get(field) for field in ['city', 'state', 'zip_code']):
            address = {
                "Line1": volunteer_data.get('address', ''),
                "City": volunteer_data.get('city', ''),
                "CountrySubDivisionCode": volunteer_data.get('state', ''),
                "PostalCode": volunteer_data.get('zip_code', '')
            }
            vendor_data["BillAddr"] = address
        
        result = self._make_api_request('POST', 'vendor', vendor_data)
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('Vendor', [{}])[0]
        return None
    
    def create_bill(self, vendor_id: str, line_items: List[Dict], due_date: str = None, memo: str = None) -> Optional[Dict]:
        """Create a bill for volunteer reimbursement"""
        bill_data = {
            "VendorRef": {"value": vendor_id},
            "TxnDate": datetime.now().strftime('%Y-%m-%d'),
            "Line": []
        }
        
        if due_date:
            bill_data["DueDate"] = due_date
        
        if memo:
            bill_data["Memo"] = memo
        
        total_amount = 0
        
        # Add line items
        for item in line_items:
            line = {
                "Amount": item['amount'],
                "DetailType": "AccountBasedExpenseLineDetail",
                "AccountBasedExpenseLineDetail": {
                    "AccountRef": {"value": item.get('account_id', settings.QUICKBOOKS_DEFAULT_EXPENSE_ACCOUNT)},
                    "BillableStatus": "NotBillable"
                }
            }
            
            if item.get('description'):
                line["Description"] = item['description']
            
            bill_data["Line"].append(line)
            total_amount += float(item['amount'])
        
        bill_data["TotalAmt"] = total_amount
        
        result = self._make_api_request('POST', 'bill', bill_data)
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('Bill', [{}])[0]
        return None
    
    def create_expense(self, vendor_id: str, account_id: str, amount: float, description: str = None, 
                     expense_date: str = None) -> Optional[Dict]:
        """Create an expense entry"""
        expense_data = {
            "PaymentType": "Cash",
            "EntityRef": {"value": vendor_id, "type": "Vendor"},
            "TxnDate": expense_date or datetime.now().strftime('%Y-%m-%d'),
            "Line": [{
                "Amount": amount,
                "DetailType": "AccountBasedExpenseLineDetail",
                "AccountBasedExpenseLineDetail": {
                    "AccountRef": {"value": account_id}
                }
            }],
            "TotalAmt": amount
        }
        
        if description:
            expense_data["Line"][0]["Description"] = description
        
        result = self._make_api_request('POST', 'purchase', expense_data)
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('Purchase', [{}])[0]
        return None
    
    def get_bill(self, bill_id: str) -> Optional[Dict]:
        """Get bill details"""
        result = self._make_api_request('GET', f'bill/{bill_id}')
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('Bill', [{}])[0]
        return None
    
    def update_bill(self, bill_id: str, bill_data: Dict) -> Optional[Dict]:
        """Update an existing bill"""
        result = self._make_api_request('PUT', f'bill', bill_data)
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('Bill', [{}])[0]
        return None
    
    def sync_volunteer_expenses(self, volunteer_data: Dict, expenses: List[Dict]) -> Dict[str, Any]:
        """Sync volunteer expenses to QuickBooks"""
        try:
            # Find or create vendor for volunteer
            vendors = self.get_vendors()
            volunteer_name = f"{volunteer_data.get('first_name', '')} {volunteer_data.get('last_name', '')}".strip()
            
            vendor = None
            for v in vendors:
                if v.get('Name') == volunteer_name:
                    vendor = v
                    break
            
            if not vendor:
                vendor = self.create_vendor(volunteer_data)
                if not vendor:
                    return {"success": False, "error": "Failed to create vendor"}
            
            vendor_id = vendor['Id']
            
            # Create bill with expenses
            line_items = []
            for expense in expenses:
                line_items.append({
                    'amount': expense['amount'],
                    'description': expense['description'],
                    'account_id': expense.get('quickbooks_account_id', settings.QUICKBOOKS_DEFAULT_EXPENSE_ACCOUNT)
                })
            
            bill = self.create_bill(
                vendor_id=vendor_id,
                line_items=line_items,
                memo=f"Volunteer expense reimbursement - {datetime.now().strftime('%Y-%m-%d')}"
            )
            
            if bill:
                return {
                    "success": True,
                    "bill_id": bill['Id'],
                    "vendor_id": vendor_id,
                    "total_amount": bill.get('TotalAmt', 0)
                }
            else:
                return {"success": False, "error": "Failed to create bill"}
                
        except Exception as e:
            logger.error(f"Error syncing volunteer expenses to QuickBooks: {e}")
            return {"success": False, "error": str(e)}