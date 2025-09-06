"""
Notion API client for syncing volunteer data
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotionClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_database_pages(self, database_id: str, 
                               filter_conditions: Optional[Dict] = None,
                               sorts: Optional[List[Dict]] = None,
                               page_size: int = 100) -> List[Dict[str, Any]]:
        """Get pages from a Notion database"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        all_pages = []
        has_more = True
        next_cursor = None

        while has_more:
            payload = {"page_size": page_size}
            
            if filter_conditions:
                payload["filter"] = filter_conditions
            if sorts:
                payload["sorts"] = sorts
            if next_cursor:
                payload["start_cursor"] = next_cursor

            try:
                async with self.session.post(f"{self.base_url}/databases/{database_id}/query",
                                           json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        all_pages.extend(data.get('results', []))
                        has_more = data.get('has_more', False)
                        next_cursor = data.get('next_cursor')
                    elif response.status == 429:
                        await asyncio.sleep(1)
                        continue
                    else:
                        error_text = await response.text()
                        logger.error(f"Notion API error {response.status}: {error_text}")
                        raise Exception(f"Notion API error: {response.status}")
            except Exception as e:
                logger.error(f"Error fetching pages from database {database_id}: {e}")
                raise

        return all_pages

    async def create_page(self, database_id: str, properties: Dict[str, Any],
                         children: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create a new page in a Notion database"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        payload = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        
        if children:
            payload["children"] = children

        try:
            async with self.session.post(f"{self.base_url}/pages", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    await asyncio.sleep(1)
                    return await self.create_page(database_id, properties, children)
                else:
                    error_text = await response.text()
                    logger.error(f"Error creating page: {error_text}")
                    raise Exception(f"Failed to create page: {response.status}")
        except Exception as e:
            logger.error(f"Error creating page in database {database_id}: {e}")
            raise

    async def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing page in Notion"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        payload = {"properties": properties}

        try:
            async with self.session.patch(f"{self.base_url}/pages/{page_id}",
                                        json=payload) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    await asyncio.sleep(1)
                    return await self.update_page(page_id, properties)
                else:
                    error_text = await response.text()
                    logger.error(f"Error updating page: {error_text}")
                    raise Exception(f"Failed to update page: {response.status}")
        except Exception as e:
            logger.error(f"Error updating page {page_id}: {e}")
            raise

    async def get_database_schema(self, database_id: str) -> Dict[str, Any]:
        """Get database schema information"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(f"{self.base_url}/databases/{database_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Schema fetch error: {error_text}")
                    raise Exception(f"Failed to get schema: {response.status}")
        except Exception as e:
            logger.error(f"Error getting schema for database {database_id}: {e}")
            raise

    def convert_to_notion_properties(self, data: Dict[str, Any],
                                   property_mapping: Dict[str, Dict]) -> Dict[str, Any]:
        """Convert standard data format to Notion properties"""
        properties = {}
        
        for field, value in data.items():
            if field in property_mapping:
                prop_config = property_mapping[field]
                prop_type = prop_config.get('type')
                
                if prop_type == 'title':
                    properties[field] = {
                        "title": [{"text": {"content": str(value) if value else ""}}]
                    }
                elif prop_type == 'rich_text':
                    properties[field] = {
                        "rich_text": [{"text": {"content": str(value) if value else ""}}]
                    }
                elif prop_type == 'email':
                    properties[field] = {"email": value if value else None}
                elif prop_type == 'phone_number':
                    properties[field] = {"phone_number": value if value else None}
                elif prop_type == 'select':
                    properties[field] = {"select": {"name": str(value)} if value else None}
                elif prop_type == 'multi_select':
                    if isinstance(value, list):
                        properties[field] = {
                            "multi_select": [{"name": str(item)} for item in value]
                        }
                    elif isinstance(value, str) and value:
                        properties[field] = {
                            "multi_select": [{"name": str(value)}]
                        }
                elif prop_type == 'number':
                    properties[field] = {"number": float(value) if value else None}
                elif prop_type == 'checkbox':
                    properties[field] = {"checkbox": bool(value)}
                elif prop_type == 'date':
                    if value:
                        properties[field] = {"date": {"start": str(value)}}
                elif prop_type == 'relation':
                    if isinstance(value, list):
                        properties[field] = {
                            "relation": [{"id": item} for item in value if item]
                        }
                    elif value:
                        properties[field] = {"relation": [{"id": str(value)}]}
                        
        return properties

    def extract_from_notion_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standard data from Notion properties"""
        extracted = {}
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type')
            
            if prop_type == 'title':
                title_content = prop_data.get('title', [])
                extracted[prop_name] = ''.join([t.get('plain_text', '') for t in title_content])
            elif prop_type == 'rich_text':
                rich_text_content = prop_data.get('rich_text', [])
                extracted[prop_name] = ''.join([t.get('plain_text', '') for t in rich_text_content])
            elif prop_type == 'email':
                extracted[prop_name] = prop_data.get('email', '')
            elif prop_type == 'phone_number':
                extracted[prop_name] = prop_data.get('phone_number', '')
            elif prop_type == 'select':
                select_data = prop_data.get('select')
                extracted[prop_name] = select_data.get('name', '') if select_data else ''
            elif prop_type == 'multi_select':
                multi_select_data = prop_data.get('multi_select', [])
                extracted[prop_name] = [item.get('name', '') for item in multi_select_data]
            elif prop_type == 'number':
                extracted[prop_name] = prop_data.get('number', 0)
            elif prop_type == 'checkbox':
                extracted[prop_name] = prop_data.get('checkbox', False)
            elif prop_type == 'date':
                date_data = prop_data.get('date')
                extracted[prop_name] = date_data.get('start', '') if date_data else ''
            elif prop_type == 'relation':
                relation_data = prop_data.get('relation', [])
                extracted[prop_name] = [item.get('id', '') for item in relation_data]
            elif prop_type == 'created_time':
                extracted[prop_name] = prop_data.get('created_time', '')
            elif prop_type == 'last_edited_time':
                extracted[prop_name] = prop_data.get('last_edited_time', '')
                
        return extracted

    def normalize_volunteer_data(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize Notion volunteer pages to standard format"""
        normalized = []
        
        for page in pages:
            properties = page.get('properties', {})
            extracted = self.extract_from_notion_properties(properties)
            
            normalized_record = {
                'id': page.get('id'),
                'name': extracted.get('Name', ''),
                'email': extracted.get('Email', ''),
                'phone': extracted.get('Phone', ''),
                'skills': extracted.get('Skills', []),
                'interests': extracted.get('Interests', []),
                'availability': extracted.get('Availability', {}),
                'branch_preference': extracted.get('Branch Preference', ''),
                'experience_level': extracted.get('Experience Level', 'Beginner'),
                'member_status': extracted.get('Member Status', False),
                'last_updated': extracted.get('Last Updated', datetime.now().isoformat()),
                'created_time': extracted.get('Created Time', ''),
                'sync_status': 'synced'
            }
            normalized.append(normalized_record)
            
        return normalized

    def normalize_project_data(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize Notion project pages to standard format"""
        normalized = []
        
        for page in pages:
            properties = page.get('properties', {})
            extracted = self.extract_from_notion_properties(properties)
            
            normalized_record = {
                'id': page.get('id'),
                'title': extracted.get('Title', ''),
                'description': extracted.get('Description', ''),
                'category': extracted.get('Category', ''),
                'branch': extracted.get('Branch', ''),
                'skills_needed': extracted.get('Skills Needed', []),
                'time_commitment': extracted.get('Time Commitment', ''),
                'status': extracted.get('Status', 'Active'),
                'contact_person': extracted.get('Contact Person', ''),
                'start_date': extracted.get('Start Date', ''),
                'end_date': extracted.get('End Date', ''),
                'volunteers_needed': extracted.get('Volunteers Needed', 0),
                'volunteers_assigned': extracted.get('Volunteers Assigned', []),
                'created_time': extracted.get('Created Time', ''),
                'last_updated': extracted.get('Last Updated', datetime.now().isoformat()),
                'sync_status': 'synced'
            }
            normalized.append(normalized_record)
            
        return normalized