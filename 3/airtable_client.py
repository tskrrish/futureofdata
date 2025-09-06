"""
Airtable API client for syncing volunteer data
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AirtableClient:
    def __init__(self, api_key: str, base_id: str):
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = f"https://api.airtable.com/v0/{base_id}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_table_records(self, table_name: str, view: Optional[str] = None, 
                              fields: Optional[List[str]] = None, 
                              max_records: int = 100) -> List[Dict[str, Any]]:
        """Get records from an Airtable table"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        params = {}
        if view:
            params['view'] = view
        if fields:
            params['fields[]'] = fields
        if max_records:
            params['maxRecords'] = max_records

        all_records = []
        offset = None

        while True:
            if offset:
                params['offset'] = offset

            try:
                async with self.session.get(f"{self.base_url}/{table_name}", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get('records', [])
                        all_records.extend(records)
                        
                        offset = data.get('offset')
                        if not offset:
                            break
                    elif response.status == 429:
                        await asyncio.sleep(0.2)
                        continue
                    else:
                        error_text = await response.text()
                        logger.error(f"Airtable API error {response.status}: {error_text}")
                        raise Exception(f"Airtable API error: {response.status}")
            except Exception as e:
                logger.error(f"Error fetching records from {table_name}: {e}")
                raise

        return all_records

    async def create_record(self, table_name: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in Airtable"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        payload = {"fields": fields}

        try:
            async with self.session.post(f"{self.base_url}/{table_name}", 
                                       json=payload) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    await asyncio.sleep(0.2)
                    return await self.create_record(table_name, fields)
                else:
                    error_text = await response.text()
                    logger.error(f"Error creating record: {error_text}")
                    raise Exception(f"Failed to create record: {response.status}")
        except Exception as e:
            logger.error(f"Error creating record in {table_name}: {e}")
            raise

    async def update_record(self, table_name: str, record_id: str, 
                          fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record in Airtable"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        payload = {"fields": fields}

        try:
            async with self.session.patch(f"{self.base_url}/{table_name}/{record_id}", 
                                        json=payload) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    await asyncio.sleep(0.2)
                    return await self.update_record(table_name, record_id, fields)
                else:
                    error_text = await response.text()
                    logger.error(f"Error updating record: {error_text}")
                    raise Exception(f"Failed to update record: {response.status}")
        except Exception as e:
            logger.error(f"Error updating record {record_id} in {table_name}: {e}")
            raise

    async def batch_create_records(self, table_name: str, 
                                 records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple records in batch (max 10 at a time)"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        all_results = []
        batch_size = 10

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            payload = {"records": [{"fields": record} for record in batch]}

            try:
                async with self.session.post(f"{self.base_url}/{table_name}", 
                                           json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        all_results.extend(data.get('records', []))
                    elif response.status == 429:
                        await asyncio.sleep(0.2)
                        i -= batch_size
                        continue
                    else:
                        error_text = await response.text()
                        logger.error(f"Batch create error: {error_text}")
                        raise Exception(f"Failed to batch create: {response.status}")
                        
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error batch creating records in {table_name}: {e}")
                raise

        return all_results

    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables") as response:
                if response.status == 200:
                    data = await response.json()
                    tables = data.get('tables', [])
                    for table in tables:
                        if table.get('name') == table_name:
                            return table
                    raise Exception(f"Table {table_name} not found")
                else:
                    error_text = await response.text()
                    logger.error(f"Schema fetch error: {error_text}")
                    raise Exception(f"Failed to get schema: {response.status}")
        except Exception as e:
            logger.error(f"Error getting schema for {table_name}: {e}")
            raise

    def normalize_volunteer_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize Airtable volunteer records to standard format"""
        normalized = []
        
        for record in records:
            fields = record.get('fields', {})
            normalized_record = {
                'id': record.get('id'),
                'name': fields.get('Name', ''),
                'email': fields.get('Email', ''),
                'phone': fields.get('Phone', ''),
                'skills': fields.get('Skills', []),
                'interests': fields.get('Interests', []),
                'availability': fields.get('Availability', {}),
                'branch_preference': fields.get('Branch Preference', ''),
                'experience_level': fields.get('Experience Level', 'Beginner'),
                'member_status': fields.get('Member Status', False),
                'last_updated': fields.get('Last Updated', datetime.now().isoformat()),
                'created_time': record.get('createdTime'),
                'sync_status': 'synced'
            }
            normalized.append(normalized_record)
            
        return normalized

    def normalize_project_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize Airtable project records to standard format"""
        normalized = []
        
        for record in records:
            fields = record.get('fields', {})
            normalized_record = {
                'id': record.get('id'),
                'title': fields.get('Title', ''),
                'description': fields.get('Description', ''),
                'category': fields.get('Category', ''),
                'branch': fields.get('Branch', ''),
                'skills_needed': fields.get('Skills Needed', []),
                'time_commitment': fields.get('Time Commitment', ''),
                'status': fields.get('Status', 'Active'),
                'contact_person': fields.get('Contact Person', ''),
                'start_date': fields.get('Start Date', ''),
                'end_date': fields.get('End Date', ''),
                'volunteers_needed': fields.get('Volunteers Needed', 0),
                'volunteers_assigned': fields.get('Volunteers Assigned', []),
                'created_time': record.get('createdTime'),
                'last_updated': fields.get('Last Updated', datetime.now().isoformat()),
                'sync_status': 'synced'
            }
            normalized.append(normalized_record)
            
        return normalized