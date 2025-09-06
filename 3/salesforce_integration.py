"""
Salesforce Nonprofit Cloud Integration
Syncs contacts, campaigns, and activities between YMCA volunteer system and Salesforce
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
import base64
import json
from dataclasses import dataclass, asdict
from pydantic import BaseModel

logger = logging.getLogger(__name__)

@dataclass
class SalesforceContact:
    """Salesforce Contact object"""
    Id: Optional[str] = None
    FirstName: Optional[str] = None
    LastName: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None
    MailingStreet: Optional[str] = None
    MailingCity: Optional[str] = None
    MailingState: Optional[str] = None
    MailingPostalCode: Optional[str] = None
    Birthdate: Optional[str] = None
    # Nonprofit Cloud specific fields
    npe01__PreferredPhone__c: Optional[str] = None
    npe01__Preferred_Email__c: Optional[str] = None
    npsp__Primary_Affiliation__c: Optional[str] = None
    Volunteer_Status__c: Optional[str] = None
    Volunteer_Skills__c: Optional[str] = None
    Volunteer_Interests__c: Optional[str] = None
    Last_Volunteer_Activity__c: Optional[str] = None

@dataclass
class SalesforceCampaign:
    """Salesforce Campaign object"""
    Id: Optional[str] = None
    Name: str = ""
    Type: Optional[str] = None
    Status: str = "Planned"
    StartDate: Optional[str] = None
    EndDate: Optional[str] = None
    Description: Optional[str] = None
    # Nonprofit Cloud specific fields
    npo02__Contacts_Responded__c: Optional[int] = None
    Volunteer_Opportunity__c: bool = False
    Required_Skills__c: Optional[str] = None
    Location__c: Optional[str] = None
    Time_Commitment_Hours__c: Optional[float] = None

@dataclass
class SalesforceActivity:
    """Salesforce Task/Activity object"""
    Id: Optional[str] = None
    Subject: str = ""
    ActivityDate: Optional[str] = None
    Status: str = "Not Started"
    Priority: str = "Normal"
    WhoId: Optional[str] = None  # Contact ID
    WhatId: Optional[str] = None  # Campaign ID
    Description: Optional[str] = None
    # Custom fields for volunteer activities
    Volunteer_Hours__c: Optional[float] = None
    Activity_Type__c: Optional[str] = None
    Branch_Location__c: Optional[str] = None

class SalesforceConfig(BaseModel):
    """Salesforce configuration"""
    instance_url: str
    client_id: str
    client_secret: str
    username: str
    password: str
    security_token: str
    api_version: str = "v58.0"
    
class SalesforceNonprofitCloudSync:
    """
    Salesforce Nonprofit Cloud synchronization service
    Handles authentication, data sync, and error handling
    """
    
    def __init__(self, config: SalesforceConfig):
        self.config = config
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.session = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        await self.authenticate()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
        
    async def authenticate(self) -> bool:
        """Authenticate with Salesforce using OAuth 2.0 Username-Password flow"""
        try:
            auth_url = f"{self.config.instance_url}/services/oauth2/token"
            
            auth_data = {
                "grant_type": "password",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "username": self.config.username,
                "password": f"{self.config.password}{self.config.security_token}"
            }
            
            response = await self.session.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            auth_result = response.json()
            self.access_token = auth_result["access_token"]
            
            # Token expires in 2 hours by default
            self.token_expires_at = datetime.now() + timedelta(hours=2)
            
            logger.info("Successfully authenticated with Salesforce")
            return True
            
        except Exception as e:
            logger.error(f"Salesforce authentication failed: {e}")
            return False
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if (not self.access_token or 
            not self.token_expires_at or 
            datetime.now() >= self.token_expires_at - timedelta(minutes=5)):
            await self.authenticate()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authorization"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _salesforce_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Salesforce API"""
        await self._ensure_authenticated()
        
        url = f"{self.config.instance_url}/services/data/{self.config.api_version}/{endpoint}"
        headers = self._get_headers()
        
        try:
            if method.upper() == "GET":
                response = await self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await self.session.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = await self.session.patch(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if response.status_code == 204:  # No Content
                return {"success": True}
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Salesforce API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    # Contact Sync Methods
    
    async def sync_contact_to_salesforce(self, volunteer_data: Dict) -> Optional[str]:
        """Sync volunteer data to Salesforce Contact"""
        try:
            # Check if contact already exists
            email = volunteer_data.get("email")
            if email:
                existing_contact = await self.find_contact_by_email(email)
                if existing_contact:
                    # Update existing contact
                    contact_id = existing_contact["Id"]
                    await self.update_contact(contact_id, volunteer_data)
                    return contact_id
            
            # Create new contact
            contact = SalesforceContact(
                FirstName=volunteer_data.get("first_name"),
                LastName=volunteer_data.get("last_name"),
                Email=volunteer_data.get("email"),
                Phone=volunteer_data.get("phone"),
                MailingCity=volunteer_data.get("city"),
                MailingState=volunteer_data.get("state"),
                MailingPostalCode=volunteer_data.get("zip_code"),
                npe01__PreferredPhone__c="Work" if volunteer_data.get("phone") else None,
                npe01__Preferred_Email__c="Personal" if volunteer_data.get("email") else None,
                Volunteer_Status__c="Active",
                Volunteer_Skills__c=volunteer_data.get("skills", ""),
                Volunteer_Interests__c=volunteer_data.get("interests", ""),
                Last_Volunteer_Activity__c=datetime.now().isoformat()
            )
            
            # Remove None values
            contact_data = {k: v for k, v in asdict(contact).items() if v is not None}
            
            result = await self._salesforce_request("POST", "sobjects/Contact", contact_data)
            contact_id = result.get("id")
            
            logger.info(f"Created Salesforce contact: {contact_id}")
            return contact_id
            
        except Exception as e:
            logger.error(f"Failed to sync contact: {e}")
            return None
    
    async def find_contact_by_email(self, email: str) -> Optional[Dict]:
        """Find Salesforce contact by email"""
        try:
            query = f"SELECT Id, FirstName, LastName, Email FROM Contact WHERE Email = '{email}' LIMIT 1"
            result = await self._salesforce_request("GET", f"query?q={query}")
            
            records = result.get("records", [])
            return records[0] if records else None
            
        except Exception as e:
            logger.error(f"Failed to find contact by email: {e}")
            return None
    
    async def update_contact(self, contact_id: str, volunteer_data: Dict) -> bool:
        """Update existing Salesforce contact"""
        try:
            update_data = {
                "Volunteer_Skills__c": volunteer_data.get("skills", ""),
                "Volunteer_Interests__c": volunteer_data.get("interests", ""),
                "Last_Volunteer_Activity__c": datetime.now().isoformat(),
                "Phone": volunteer_data.get("phone"),
                "MailingCity": volunteer_data.get("city"),
                "MailingState": volunteer_data.get("state"),
                "MailingPostalCode": volunteer_data.get("zip_code")
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            await self._salesforce_request("PATCH", f"sobjects/Contact/{contact_id}", update_data)
            
            logger.info(f"Updated Salesforce contact: {contact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update contact: {e}")
            return False
    
    # Campaign Sync Methods
    
    async def sync_campaign_to_salesforce(self, project_data: Dict) -> Optional[str]:
        """Sync volunteer project/opportunity to Salesforce Campaign"""
        try:
            # Check if campaign already exists by name
            existing_campaign = await self.find_campaign_by_name(project_data.get("name", ""))
            if existing_campaign:
                campaign_id = existing_campaign["Id"]
                await self.update_campaign(campaign_id, project_data)
                return campaign_id
            
            # Create new campaign
            campaign = SalesforceCampaign(
                Name=project_data.get("name", "Volunteer Opportunity"),
                Type="Volunteer",
                Status="Active",
                StartDate=project_data.get("start_date"),
                EndDate=project_data.get("end_date"),
                Description=project_data.get("description", ""),
                Volunteer_Opportunity__c=True,
                Required_Skills__c=project_data.get("required_skills", ""),
                Location__c=project_data.get("branch", ""),
                Time_Commitment_Hours__c=project_data.get("estimated_hours")
            )
            
            # Remove None values
            campaign_data = {k: v for k, v in asdict(campaign).items() if v is not None}
            
            result = await self._salesforce_request("POST", "sobjects/Campaign", campaign_data)
            campaign_id = result.get("id")
            
            logger.info(f"Created Salesforce campaign: {campaign_id}")
            return campaign_id
            
        except Exception as e:
            logger.error(f"Failed to sync campaign: {e}")
            return None
    
    async def find_campaign_by_name(self, name: str) -> Optional[Dict]:
        """Find Salesforce campaign by name"""
        try:
            # Escape single quotes in name
            escaped_name = name.replace("'", "\\'")
            query = f"SELECT Id, Name, Status FROM Campaign WHERE Name = '{escaped_name}' LIMIT 1"
            result = await self._salesforce_request("GET", f"query?q={query}")
            
            records = result.get("records", [])
            return records[0] if records else None
            
        except Exception as e:
            logger.error(f"Failed to find campaign by name: {e}")
            return None
    
    async def update_campaign(self, campaign_id: str, project_data: Dict) -> bool:
        """Update existing Salesforce campaign"""
        try:
            update_data = {
                "Description": project_data.get("description", ""),
                "Required_Skills__c": project_data.get("required_skills", ""),
                "Location__c": project_data.get("branch", ""),
                "Time_Commitment_Hours__c": project_data.get("estimated_hours"),
                "EndDate": project_data.get("end_date")
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            await self._salesforce_request("PATCH", f"sobjects/Campaign/{campaign_id}", update_data)
            
            logger.info(f"Updated Salesforce campaign: {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update campaign: {e}")
            return False
    
    # Activity Sync Methods
    
    async def sync_activity_to_salesforce(self, activity_data: Dict) -> Optional[str]:
        """Sync volunteer activity to Salesforce Task"""
        try:
            activity = SalesforceActivity(
                Subject=activity_data.get("subject", "Volunteer Activity"),
                ActivityDate=activity_data.get("date"),
                Status="Completed",
                Priority="Normal",
                WhoId=activity_data.get("contact_id"),  # Salesforce Contact ID
                WhatId=activity_data.get("campaign_id"),  # Salesforce Campaign ID
                Description=activity_data.get("description", ""),
                Volunteer_Hours__c=activity_data.get("hours", 0),
                Activity_Type__c=activity_data.get("activity_type", "Volunteer Work"),
                Branch_Location__c=activity_data.get("branch", "")
            )
            
            # Remove None values
            activity_data_clean = {k: v for k, v in asdict(activity).items() if v is not None}
            
            result = await self._salesforce_request("POST", "sobjects/Task", activity_data_clean)
            activity_id = result.get("id")
            
            logger.info(f"Created Salesforce activity: {activity_id}")
            return activity_id
            
        except Exception as e:
            logger.error(f"Failed to sync activity: {e}")
            return None
    
    # Bulk Operations
    
    async def bulk_sync_contacts(self, volunteer_list: List[Dict]) -> Dict[str, Any]:
        """Bulk sync multiple contacts to Salesforce"""
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for volunteer in volunteer_list:
            try:
                contact_id = await self.sync_contact_to_salesforce(volunteer)
                if contact_id:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to sync {volunteer.get('email', 'Unknown')}")
                    
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error syncing {volunteer.get('email', 'Unknown')}: {str(e)}")
        
        return results
    
    async def bulk_sync_campaigns(self, project_list: List[Dict]) -> Dict[str, Any]:
        """Bulk sync multiple campaigns to Salesforce"""
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for project in project_list:
            try:
                campaign_id = await self.sync_campaign_to_salesforce(project)
                if campaign_id:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to sync {project.get('name', 'Unknown')}")
                    
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error syncing {project.get('name', 'Unknown')}: {str(e)}")
        
        return results
    
    # Query Methods
    
    async def get_recent_activities(self, days: int = 30) -> List[Dict]:
        """Get recent volunteer activities from Salesforce"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()[:10]
            
            query = f"""
                SELECT Id, Subject, ActivityDate, Status, WhoId, WhatId, 
                       Volunteer_Hours__c, Activity_Type__c, Branch_Location__c
                FROM Task 
                WHERE ActivityDate >= {cutoff_date} 
                AND Activity_Type__c = 'Volunteer Work'
                ORDER BY ActivityDate DESC
            """
            
            result = await self._salesforce_request("GET", f"query?q={query}")
            return result.get("records", [])
            
        except Exception as e:
            logger.error(f"Failed to get recent activities: {e}")
            return []
    
    async def get_active_campaigns(self) -> List[Dict]:
        """Get active volunteer campaigns from Salesforce"""
        try:
            query = """
                SELECT Id, Name, Status, StartDate, EndDate, Description,
                       Volunteer_Opportunity__c, Required_Skills__c, Location__c
                FROM Campaign 
                WHERE Status = 'Active' 
                AND Volunteer_Opportunity__c = true
                ORDER BY StartDate DESC
            """
            
            result = await self._salesforce_request("GET", f"query?q={query}")
            return result.get("records", [])
            
        except Exception as e:
            logger.error(f"Failed to get active campaigns: {e}")
            return []
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Salesforce connection and return system info"""
        try:
            await self._ensure_authenticated()
            
            # Get org info
            result = await self._salesforce_request("GET", "")
            
            # Get user info
            query = "SELECT Id, Name, Email FROM User WHERE Id = UserInfo.getUserId()"
            user_result = await self._salesforce_request("GET", f"query?q={query}")
            user_info = user_result.get("records", [{}])[0]
            
            return {
                "connected": True,
                "instance_url": self.config.instance_url,
                "api_version": self.config.api_version,
                "user_name": user_info.get("Name"),
                "user_email": user_info.get("Email"),
                "org_id": result.get("identity", {}).get("organization_id"),
                "last_test": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "connected": False,
                "error": str(e),
                "last_test": datetime.now().isoformat()
            }


# Utility functions for data transformation

def transform_volunteer_to_salesforce(volunteer_data: Dict) -> Dict:
    """Transform YMCA volunteer data to Salesforce Contact format"""
    return {
        "first_name": volunteer_data.get("first_name"),
        "last_name": volunteer_data.get("last_name"), 
        "email": volunteer_data.get("email"),
        "phone": volunteer_data.get("phone"),
        "city": volunteer_data.get("city"),
        "state": volunteer_data.get("state"),
        "zip_code": volunteer_data.get("zip_code"),
        "skills": volunteer_data.get("skills", ""),
        "interests": volunteer_data.get("interests", "")
    }

def transform_project_to_salesforce(project_data: Dict) -> Dict:
    """Transform YMCA project data to Salesforce Campaign format"""
    return {
        "name": project_data.get("project_clean", project_data.get("name", "")),
        "description": project_data.get("description", ""),
        "branch": project_data.get("branch_short", ""),
        "required_skills": project_data.get("category", ""),
        "estimated_hours": project_data.get("estimated_hours"),
        "start_date": project_data.get("start_date"),
        "end_date": project_data.get("end_date")
    }

def transform_activity_to_salesforce(interaction_data: Dict, contact_id: str, campaign_id: str) -> Dict:
    """Transform YMCA interaction data to Salesforce Task format"""
    return {
        "subject": f"Volunteer Activity - {interaction_data.get('project_clean', 'Unknown Project')}",
        "date": interaction_data.get("date"),
        "contact_id": contact_id,
        "campaign_id": campaign_id,
        "description": f"Volunteer work at {interaction_data.get('branch_short', 'Unknown Branch')}",
        "hours": interaction_data.get("hours", 0),
        "activity_type": "Volunteer Work",
        "branch": interaction_data.get("branch_short", "")
    }