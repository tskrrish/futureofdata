"""
Bidirectional sync service for Airtable and Notion integration
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging
from enum import Enum

from airtable_client import AirtableClient
from notion_client import NotionClient

logger = logging.getLogger(__name__)

class SyncDirection(Enum):
    AIRTABLE_TO_NOTION = "airtable_to_notion"
    NOTION_TO_AIRTABLE = "notion_to_airtable"
    BIDIRECTIONAL = "bidirectional"

class SyncStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"

@dataclass
class SyncConfig:
    airtable_api_key: str
    airtable_base_id: str
    notion_api_key: str
    volunteer_table_name: str
    project_table_name: str
    notion_volunteer_db_id: str
    notion_project_db_id: str
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    sync_interval_minutes: int = 30
    batch_size: int = 50
    conflict_resolution: str = "notion_wins"  # or "airtable_wins" or "manual"
    field_mappings: Dict[str, Dict] = None

@dataclass
class SyncRecord:
    id: str
    source: str  # 'airtable' or 'notion'
    table_type: str  # 'volunteers' or 'projects'
    data: Dict[str, Any]
    last_modified: datetime
    sync_status: SyncStatus = SyncStatus.PENDING
    error_message: Optional[str] = None
    conflict_data: Optional[Dict] = None

class CollaborationSyncService:
    def __init__(self, config: SyncConfig):
        self.config = config
        self.sync_history: List[Dict] = []
        self.conflict_queue: List[SyncRecord] = []
        self.is_syncing = False
        
        # Property mappings for different platforms
        self.volunteer_property_mappings = {
            'notion': {
                'Name': {'type': 'title'},
                'Email': {'type': 'email'},
                'Phone': {'type': 'phone_number'},
                'Skills': {'type': 'multi_select'},
                'Interests': {'type': 'multi_select'},
                'Branch Preference': {'type': 'select'},
                'Experience Level': {'type': 'select'},
                'Member Status': {'type': 'checkbox'},
                'Last Updated': {'type': 'date'},
                'Sync Status': {'type': 'select'}
            },
            'airtable': {
                'Name': 'Single line text',
                'Email': 'Email',
                'Phone': 'Phone number',
                'Skills': 'Multiple select',
                'Interests': 'Multiple select',
                'Branch Preference': 'Single select',
                'Experience Level': 'Single select',
                'Member Status': 'Checkbox',
                'Last Updated': 'Date',
                'Sync Status': 'Single select'
            }
        }
        
        self.project_property_mappings = {
            'notion': {
                'Title': {'type': 'title'},
                'Description': {'type': 'rich_text'},
                'Category': {'type': 'select'},
                'Branch': {'type': 'select'},
                'Skills Needed': {'type': 'multi_select'},
                'Time Commitment': {'type': 'select'},
                'Status': {'type': 'select'},
                'Contact Person': {'type': 'rich_text'},
                'Start Date': {'type': 'date'},
                'End Date': {'type': 'date'},
                'Volunteers Needed': {'type': 'number'},
                'Volunteers Assigned': {'type': 'relation'},
                'Last Updated': {'type': 'date'},
                'Sync Status': {'type': 'select'}
            }
        }

    async def start_sync_process(self, table_types: List[str] = None) -> Dict[str, Any]:
        """Start the bidirectional sync process"""
        if self.is_syncing:
            return {"status": "error", "message": "Sync already in progress"}

        self.is_syncing = True
        table_types = table_types or ['volunteers', 'projects']
        
        try:
            sync_results = {
                "start_time": datetime.now().isoformat(),
                "tables_synced": [],
                "records_processed": 0,
                "conflicts_detected": 0,
                "errors": []
            }

            async with AirtableClient(self.config.airtable_api_key, 
                                    self.config.airtable_base_id) as airtable:
                async with NotionClient(self.config.notion_api_key) as notion:
                    
                    for table_type in table_types:
                        table_result = await self._sync_table(airtable, notion, table_type)
                        sync_results["tables_synced"].append(table_result)
                        sync_results["records_processed"] += table_result.get("records_processed", 0)
                        sync_results["conflicts_detected"] += table_result.get("conflicts_detected", 0)
                        sync_results["errors"].extend(table_result.get("errors", []))

            sync_results["end_time"] = datetime.now().isoformat()
            sync_results["duration_seconds"] = (
                datetime.fromisoformat(sync_results["end_time"]) - 
                datetime.fromisoformat(sync_results["start_time"])
            ).total_seconds()

            self.sync_history.append(sync_results)
            
            logger.info(f"Sync completed: {sync_results['records_processed']} records processed, "
                       f"{sync_results['conflicts_detected']} conflicts detected")

            return sync_results

        except Exception as e:
            logger.error(f"Sync process failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "end_time": datetime.now().isoformat()
            }
        finally:
            self.is_syncing = False

    async def _sync_table(self, airtable: AirtableClient, notion: NotionClient, 
                         table_type: str) -> Dict[str, Any]:
        """Sync a specific table between Airtable and Notion"""
        logger.info(f"Starting sync for {table_type} table")
        
        result = {
            "table_type": table_type,
            "records_processed": 0,
            "conflicts_detected": 0,
            "errors": [],
            "created": 0,
            "updated": 0,
            "skipped": 0
        }

        try:
            # Get data from both sources
            if table_type == 'volunteers':
                airtable_records = await airtable.get_table_records(
                    self.config.volunteer_table_name
                )
                notion_pages = await notion.get_database_pages(
                    self.config.notion_volunteer_db_id
                )
                airtable_normalized = airtable.normalize_volunteer_data(airtable_records)
                notion_normalized = notion.normalize_volunteer_data(notion_pages)
                
            elif table_type == 'projects':
                airtable_records = await airtable.get_table_records(
                    self.config.project_table_name
                )
                notion_pages = await notion.get_database_pages(
                    self.config.notion_project_db_id
                )
                airtable_normalized = airtable.normalize_project_data(airtable_records)
                notion_normalized = notion.normalize_project_data(notion_pages)
            else:
                raise ValueError(f"Unknown table type: {table_type}")

            # Create lookup maps
            airtable_map = {record.get('name', '') + record.get('email', ''): record 
                           for record in airtable_normalized}
            notion_map = {record.get('name', '') + record.get('email', ''): record 
                         for record in notion_normalized}

            # Sync from Airtable to Notion
            if self.config.sync_direction in [SyncDirection.AIRTABLE_TO_NOTION, 
                                            SyncDirection.BIDIRECTIONAL]:
                airtable_result = await self._sync_direction(
                    airtable, notion, airtable_normalized, notion_map, 
                    'airtable_to_notion', table_type
                )
                result["created"] += airtable_result["created"]
                result["updated"] += airtable_result["updated"]
                result["conflicts_detected"] += airtable_result["conflicts"]

            # Sync from Notion to Airtable
            if self.config.sync_direction in [SyncDirection.NOTION_TO_AIRTABLE, 
                                            SyncDirection.BIDIRECTIONAL]:
                notion_result = await self._sync_direction(
                    airtable, notion, notion_normalized, airtable_map, 
                    'notion_to_airtable', table_type
                )
                result["created"] += notion_result["created"]
                result["updated"] += notion_result["updated"]
                result["conflicts_detected"] += notion_result["conflicts"]

            result["records_processed"] = len(airtable_normalized) + len(notion_normalized)

        except Exception as e:
            logger.error(f"Error syncing {table_type} table: {e}")
            result["errors"].append(str(e))

        return result

    async def _sync_direction(self, airtable: AirtableClient, notion: NotionClient,
                            source_records: List[Dict], target_map: Dict[str, Dict],
                            direction: str, table_type: str) -> Dict[str, int]:
        """Sync records in one direction"""
        result = {"created": 0, "updated": 0, "conflicts": 0}
        
        for record in source_records:
            try:
                key = record.get('name', '') + record.get('email', '')
                existing_record = target_map.get(key)
                
                if existing_record:
                    # Check for conflicts
                    if await self._has_conflict(record, existing_record):
                        await self._handle_conflict(record, existing_record, direction, table_type)
                        result["conflicts"] += 1
                        continue
                    
                    # Update existing record
                    if direction == 'airtable_to_notion':
                        await self._update_notion_record(notion, existing_record['id'], 
                                                       record, table_type)
                    else:
                        await self._update_airtable_record(airtable, existing_record['id'], 
                                                         record, table_type)
                    result["updated"] += 1
                else:
                    # Create new record
                    if direction == 'airtable_to_notion':
                        await self._create_notion_record(notion, record, table_type)
                    else:
                        await self._create_airtable_record(airtable, record, table_type)
                    result["created"] += 1
                    
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error processing record {record.get('name', 'unknown')}: {e}")
                
        return result

    async def _has_conflict(self, record1: Dict, record2: Dict) -> bool:
        """Check if two records have conflicting updates"""
        record1_time = datetime.fromisoformat(record1.get('last_updated', '1970-01-01'))
        record2_time = datetime.fromisoformat(record2.get('last_updated', '1970-01-01'))
        
        time_diff = abs((record1_time - record2_time).total_seconds())
        
        # If both records were updated within 5 minutes, consider it a conflict
        if time_diff < 300:  # 5 minutes
            return True
            
        # Check for data conflicts
        key_fields = ['name', 'email', 'phone', 'skills', 'interests']
        for field in key_fields:
            if record1.get(field) != record2.get(field) and record1.get(field) and record2.get(field):
                return True
                
        return False

    async def _handle_conflict(self, record1: Dict, record2: Dict, 
                             direction: str, table_type: str):
        """Handle sync conflicts based on configuration"""
        conflict_record = SyncRecord(
            id=f"{record1.get('id', '')}_{record2.get('id', '')}",
            source=direction.split('_to_')[0],
            table_type=table_type,
            data=record1,
            last_modified=datetime.now(),
            sync_status=SyncStatus.CONFLICT,
            conflict_data={
                "source_record": record1,
                "target_record": record2,
                "direction": direction
            }
        )
        
        if self.config.conflict_resolution == "manual":
            self.conflict_queue.append(conflict_record)
        elif self.config.conflict_resolution == "notion_wins" and "notion" in direction:
            # Apply Notion record
            pass
        elif self.config.conflict_resolution == "airtable_wins" and "airtable" in direction:
            # Apply Airtable record
            pass
        
        logger.warning(f"Conflict detected for {record1.get('name', 'unknown')}")

    async def _create_notion_record(self, notion: NotionClient, record: Dict, table_type: str):
        """Create a new record in Notion"""
        database_id = (self.config.notion_volunteer_db_id if table_type == 'volunteers' 
                      else self.config.notion_project_db_id)
        
        property_mapping = (self.volunteer_property_mappings['notion'] if table_type == 'volunteers'
                          else self.project_property_mappings['notion'])
        
        properties = notion.convert_to_notion_properties(record, property_mapping)
        properties['Sync Status'] = {"select": {"name": "synced_from_airtable"}}
        properties['Last Updated'] = {"date": {"start": datetime.now().isoformat()}}
        
        await notion.create_page(database_id, properties)

    async def _update_notion_record(self, notion: NotionClient, page_id: str, 
                                  record: Dict, table_type: str):
        """Update an existing record in Notion"""
        property_mapping = (self.volunteer_property_mappings['notion'] if table_type == 'volunteers'
                          else self.project_property_mappings['notion'])
        
        properties = notion.convert_to_notion_properties(record, property_mapping)
        properties['Sync Status'] = {"select": {"name": "synced_from_airtable"}}
        properties['Last Updated'] = {"date": {"start": datetime.now().isoformat()}}
        
        await notion.update_page(page_id, properties)

    async def _create_airtable_record(self, airtable: AirtableClient, record: Dict, table_type: str):
        """Create a new record in Airtable"""
        table_name = (self.config.volunteer_table_name if table_type == 'volunteers' 
                     else self.config.project_table_name)
        
        # Convert record to Airtable format
        fields = dict(record)
        fields['Sync Status'] = 'synced_from_notion'
        fields['Last Updated'] = datetime.now().isoformat()
        
        await airtable.create_record(table_name, fields)

    async def _update_airtable_record(self, airtable: AirtableClient, record_id: str,
                                    record: Dict, table_type: str):
        """Update an existing record in Airtable"""
        table_name = (self.config.volunteer_table_name if table_type == 'volunteers' 
                     else self.config.project_table_name)
        
        # Convert record to Airtable format
        fields = dict(record)
        fields['Sync Status'] = 'synced_from_notion'
        fields['Last Updated'] = datetime.now().isoformat()
        
        await airtable.update_record(table_name, record_id, fields)

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and statistics"""
        return {
            "is_syncing": self.is_syncing,
            "last_sync": self.sync_history[-1] if self.sync_history else None,
            "total_syncs": len(self.sync_history),
            "conflicts_pending": len(self.conflict_queue),
            "conflict_queue": [asdict(record) for record in self.conflict_queue]
        }

    async def resolve_conflict(self, conflict_id: str, resolution: str, 
                             resolved_data: Optional[Dict] = None) -> bool:
        """Resolve a specific conflict"""
        for i, conflict in enumerate(self.conflict_queue):
            if conflict.id == conflict_id:
                if resolution == "accept_source":
                    # Apply source record
                    pass
                elif resolution == "accept_target":
                    # Apply target record
                    pass
                elif resolution == "custom" and resolved_data:
                    # Apply custom resolution
                    pass
                
                # Remove from conflict queue
                self.conflict_queue.pop(i)
                logger.info(f"Conflict {conflict_id} resolved with resolution: {resolution}")
                return True
        
        return False

    def get_field_mappings(self) -> Dict[str, Dict]:
        """Get field mappings for both platforms"""
        return {
            "volunteer_mappings": self.volunteer_property_mappings,
            "project_mappings": self.project_property_mappings
        }