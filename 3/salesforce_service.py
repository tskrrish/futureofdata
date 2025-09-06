"""
Salesforce Service Manager
Manages Salesforce synchronization operations and provides high-level interface
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from contextlib import asynccontextmanager

from salesforce_integration import SalesforceNonprofitCloudSync, SalesforceConfig
from salesforce_integration import transform_volunteer_to_salesforce, transform_project_to_salesforce, transform_activity_to_salesforce
from config import settings

logger = logging.getLogger(__name__)

class SalesforceService:
    """
    High-level service for managing Salesforce Nonprofit Cloud integration
    """
    
    def __init__(self):
        self.config = None
        self.last_sync_time: Optional[datetime] = None
        self.sync_in_progress = False
        self._initialize_config()
    
    def _initialize_config(self):
        """Initialize Salesforce configuration from settings"""
        if not settings.SALESFORCE_SYNC_ENABLED:
            logger.info("Salesforce sync is disabled")
            return
            
        try:
            self.config = SalesforceConfig(
                instance_url=settings.SALESFORCE_INSTANCE_URL,
                client_id=settings.SALESFORCE_CLIENT_ID,
                client_secret=settings.SALESFORCE_CLIENT_SECRET,
                username=settings.SALESFORCE_USERNAME,
                password=settings.SALESFORCE_PASSWORD,
                security_token=settings.SALESFORCE_SECURITY_TOKEN,
                api_version=settings.SALESFORCE_API_VERSION
            )
            logger.info("Salesforce configuration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Salesforce config: {e}")
            self.config = None
    
    def is_enabled(self) -> bool:
        """Check if Salesforce sync is enabled and configured"""
        return self.config is not None and settings.SALESFORCE_SYNC_ENABLED
    
    @asynccontextmanager
    async def get_salesforce_client(self):
        """Get authenticated Salesforce client"""
        if not self.config:
            raise ValueError("Salesforce not configured")
        
        async with SalesforceNonprofitCloudSync(self.config) as client:
            yield client
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Salesforce connection"""
        if not self.is_enabled():
            return {
                "connected": False,
                "error": "Salesforce sync is not enabled or configured",
                "last_test": datetime.now().isoformat()
            }
        
        try:
            async with self.get_salesforce_client() as client:
                return await client.test_connection()
        except Exception as e:
            logger.error(f"Salesforce connection test failed: {e}")
            return {
                "connected": False,
                "error": str(e),
                "last_test": datetime.now().isoformat()
            }
    
    async def sync_volunteer_data(self, volunteer_data: Dict) -> Dict[str, Any]:
        """
        Full sync of volunteer data to Salesforce
        Syncs contacts, campaigns, and activities
        """
        if not self.is_enabled():
            return {"success": False, "error": "Salesforce sync not enabled"}
        
        if self.sync_in_progress:
            return {"success": False, "error": "Sync already in progress"}
        
        self.sync_in_progress = True
        start_time = datetime.now()
        
        try:
            async with self.get_salesforce_client() as client:
                results = {
                    "start_time": start_time.isoformat(),
                    "contacts": {"successful": 0, "failed": 0, "errors": []},
                    "campaigns": {"successful": 0, "failed": 0, "errors": []},
                    "activities": {"successful": 0, "failed": 0, "errors": []},
                    "total_processed": 0
                }
                
                # 1. Sync Contacts (Volunteers)
                if "volunteers" in volunteer_data:
                    logger.info("Syncing contacts to Salesforce...")
                    volunteers_df = volunteer_data["volunteers"]
                    
                    # Convert to list of dicts for processing
                    volunteer_list = []
                    for _, row in volunteers_df.iterrows():
                        volunteer_dict = transform_volunteer_to_salesforce(row.to_dict())
                        if volunteer_dict.get("email"):  # Only sync if email exists
                            volunteer_list.append(volunteer_dict)
                    
                    # Process in batches
                    batch_size = settings.SALESFORCE_BATCH_SIZE
                    for i in range(0, len(volunteer_list), batch_size):
                        batch = volunteer_list[i:i+batch_size]
                        batch_result = await client.bulk_sync_contacts(batch)
                        
                        results["contacts"]["successful"] += batch_result["successful"]
                        results["contacts"]["failed"] += batch_result["failed"]
                        results["contacts"]["errors"].extend(batch_result["errors"])
                        
                        logger.info(f"Processed contact batch {i//batch_size + 1}: {batch_result['successful']} successful, {batch_result['failed']} failed")
                
                # 2. Sync Campaigns (Projects)
                if "projects" in volunteer_data:
                    logger.info("Syncing campaigns to Salesforce...")
                    projects_df = volunteer_data["projects"]
                    
                    # Convert to list of dicts for processing
                    project_list = []
                    for _, row in projects_df.iterrows():
                        project_dict = transform_project_to_salesforce(row.to_dict())
                        if project_dict.get("name"):  # Only sync if name exists
                            project_list.append(project_dict)
                    
                    # Process in batches
                    for i in range(0, len(project_list), batch_size):
                        batch = project_list[i:i+batch_size]
                        batch_result = await client.bulk_sync_campaigns(batch)
                        
                        results["campaigns"]["successful"] += batch_result["successful"]
                        results["campaigns"]["failed"] += batch_result["failed"]
                        results["campaigns"]["errors"].extend(batch_result["errors"])
                        
                        logger.info(f"Processed campaign batch {i//batch_size + 1}: {batch_result['successful']} successful, {batch_result['failed']} failed")
                
                # 3. Sync Activities (Interactions)
                if "interactions" in volunteer_data:
                    logger.info("Syncing activities to Salesforce...")
                    interactions_df = volunteer_data["interactions"]
                    
                    # For activities, we need to map volunteers and projects to Salesforce IDs
                    # This is a simplified approach - in production you'd want to cache these mappings
                    activity_count = 0
                    activity_errors = []
                    
                    # Process a sample of recent activities to avoid overwhelming the API
                    recent_interactions = interactions_df.head(100)  # Limit to 100 most recent
                    
                    for _, row in recent_interactions.iterrows():
                        try:
                            # Find corresponding contact and campaign in Salesforce
                            contact_email = row.get("email") if "email" in row else None
                            project_name = row.get("project_clean", "")
                            
                            if not contact_email or not project_name:
                                continue
                            
                            # Look up Salesforce IDs
                            contact = await client.find_contact_by_email(contact_email)
                            campaign = await client.find_campaign_by_name(project_name)
                            
                            if contact and campaign:
                                activity_dict = transform_activity_to_salesforce(
                                    row.to_dict(),
                                    contact["Id"],
                                    campaign["Id"]
                                )
                                
                                activity_id = await client.sync_activity_to_salesforce(activity_dict)
                                if activity_id:
                                    activity_count += 1
                                else:
                                    activity_errors.append(f"Failed to create activity for {contact_email}")
                            
                        except Exception as e:
                            activity_errors.append(f"Error processing activity: {str(e)}")
                    
                    results["activities"]["successful"] = activity_count
                    results["activities"]["failed"] = len(activity_errors)
                    results["activities"]["errors"] = activity_errors[:10]  # Limit error list
                
                # Calculate totals
                results["total_processed"] = (
                    results["contacts"]["successful"] + results["contacts"]["failed"] +
                    results["campaigns"]["successful"] + results["campaigns"]["failed"] +
                    results["activities"]["successful"] + results["activities"]["failed"]
                )
                
                end_time = datetime.now()
                results["end_time"] = end_time.isoformat()
                results["duration_seconds"] = (end_time - start_time).total_seconds()
                results["success"] = True
                
                self.last_sync_time = end_time
                
                logger.info(f"Salesforce sync completed in {results['duration_seconds']:.1f}s. Processed {results['total_processed']} records")
                return results
                
        except Exception as e:
            logger.error(f"Salesforce sync failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
        finally:
            self.sync_in_progress = False
    
    async def sync_single_volunteer(self, volunteer_data: Dict) -> Dict[str, Any]:
        """Sync a single volunteer to Salesforce"""
        if not self.is_enabled():
            return {"success": False, "error": "Salesforce sync not enabled"}
        
        try:
            async with self.get_salesforce_client() as client:
                contact_id = await client.sync_contact_to_salesforce(volunteer_data)
                
                return {
                    "success": contact_id is not None,
                    "contact_id": contact_id,
                    "synced_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to sync volunteer: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_single_project(self, project_data: Dict) -> Dict[str, Any]:
        """Sync a single project to Salesforce"""
        if not self.is_enabled():
            return {"success": False, "error": "Salesforce sync not enabled"}
        
        try:
            async with self.get_salesforce_client() as client:
                campaign_id = await client.sync_campaign_to_salesforce(project_data)
                
                return {
                    "success": campaign_id is not None,
                    "campaign_id": campaign_id,
                    "synced_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to sync project: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and statistics"""
        return {
            "enabled": self.is_enabled(),
            "sync_in_progress": self.sync_in_progress,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "sync_interval_hours": settings.SALESFORCE_SYNC_INTERVAL_HOURS,
            "batch_size": settings.SALESFORCE_BATCH_SIZE,
            "needs_sync": (
                self.last_sync_time is None or 
                datetime.now() - self.last_sync_time > timedelta(hours=settings.SALESFORCE_SYNC_INTERVAL_HOURS)
            ) if self.is_enabled() else False
        }
    
    async def get_salesforce_data_summary(self) -> Dict[str, Any]:
        """Get summary of data in Salesforce"""
        if not self.is_enabled():
            return {"error": "Salesforce sync not enabled"}
        
        try:
            async with self.get_salesforce_client() as client:
                # Get counts of key objects
                contact_count_query = "SELECT COUNT() FROM Contact WHERE Volunteer_Status__c != NULL"
                campaign_count_query = "SELECT COUNT() FROM Campaign WHERE Volunteer_Opportunity__c = true"
                activity_count_query = "SELECT COUNT() FROM Task WHERE Activity_Type__c = 'Volunteer Work'"
                
                contact_result = await client._salesforce_request("GET", f"query?q={contact_count_query}")
                campaign_result = await client._salesforce_request("GET", f"query?q={campaign_count_query}")
                activity_result = await client._salesforce_request("GET", f"query?q={activity_count_query}")
                
                return {
                    "volunteer_contacts": contact_result.get("totalSize", 0),
                    "volunteer_campaigns": campaign_result.get("totalSize", 0), 
                    "volunteer_activities": activity_result.get("totalSize", 0),
                    "retrieved_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get Salesforce data summary: {e}")
            return {"error": str(e)}
    
    async def should_auto_sync(self) -> bool:
        """Check if automatic sync should be triggered"""
        if not self.is_enabled() or self.sync_in_progress:
            return False
        
        if self.last_sync_time is None:
            return True
        
        time_since_last_sync = datetime.now() - self.last_sync_time
        return time_since_last_sync > timedelta(hours=settings.SALESFORCE_SYNC_INTERVAL_HOURS)
    
    async def trigger_background_sync(self, volunteer_data: Dict) -> None:
        """Trigger background sync without waiting for completion"""
        if await self.should_auto_sync():
            logger.info("Triggering background Salesforce sync...")
            # Fire and forget - sync runs in background
            asyncio.create_task(self.sync_volunteer_data(volunteer_data))


# Global instance
salesforce_service = SalesforceService()