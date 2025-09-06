"""
External BI Connectors for Power BI, Looker, and GSuite
Handles data exports and refresh operations for external Business Intelligence tools
"""

import json
import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import pandas as pd
from pydantic import BaseModel, Field
import requests
from dataclasses import dataclass
import logging

# Configure logging
logger = logging.getLogger(__name__)

class ConnectorType(str, Enum):
    POWER_BI = "power_bi"
    LOOKER = "looker"
    GOOGLE_SHEETS = "google_sheets"

class RefreshStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    PARQUET = "parquet"

@dataclass
class ConnectorConfig:
    """Configuration for BI connector"""
    name: str
    connector_type: ConnectorType
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    workspace_id: Optional[str] = None
    dataset_id: Optional[str] = None
    table_id: Optional[str] = None
    refresh_token: Optional[str] = None
    service_account_key: Optional[Dict] = None
    base_url: Optional[str] = None
    custom_config: Optional[Dict] = None

class ExportJob(BaseModel):
    """Model for export job tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connector_name: str
    connector_type: ConnectorType
    status: RefreshStatus = RefreshStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    export_format: ExportFormat = ExportFormat.JSON
    record_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    metadata: Optional[Dict] = None

class RefreshSchedule(BaseModel):
    """Model for refresh scheduling"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connector_name: str
    cron_expression: str  # e.g., "0 */6 * * *" for every 6 hours
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

class BIConnectorInterface(ABC):
    """Abstract base class for all BI connectors"""
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.name = config.name
        self.connector_type = config.connector_type
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the BI service"""
        pass
    
    @abstractmethod
    async def export_data(self, data: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Export data to the BI service"""
        pass
    
    @abstractmethod
    async def refresh_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Trigger refresh of dataset in BI service"""
        pass
    
    @abstractmethod
    async def get_refresh_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of refresh job"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to BI service"""
        pass

class PowerBIConnector(BIConnectorInterface):
    """Power BI connector implementation"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.token_url = "https://login.microsoftonline.com/common/oauth2/token"
        self.api_base = "https://api.powerbi.com/v1.0/myorg"
        self.access_token = None
        self.token_expires_at = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Power BI API using client credentials"""
        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "resource": "https://analysis.windows.net/powerbi/api"
            }
            
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info(f"Power BI authentication successful for {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Power BI authentication failed for {self.name}: {e}")
            return False
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            await self.authenticate()
    
    async def export_data(self, data: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Export data to Power BI dataset"""
        try:
            await self._ensure_authenticated()
            
            # Convert DataFrame to Power BI format
            rows = []
            for _, row in data.iterrows():
                row_dict = {}
                for col, val in row.items():
                    if pd.isna(val):
                        row_dict[col] = None
                    elif isinstance(val, (pd.Timestamp, datetime)):
                        row_dict[col] = val.isoformat()
                    else:
                        row_dict[col] = val
                rows.append(row_dict)
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "rows": rows
            }
            
            url = f"{self.api_base}/datasets/{self.config.dataset_id}/tables/{table_name}/rows"
            
            # Clear existing rows first
            delete_response = requests.delete(url, headers=headers)
            delete_response.raise_for_status()
            
            # Add new rows
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            return {
                "success": True,
                "message": f"Successfully exported {len(rows)} rows to Power BI table {table_name}",
                "record_count": len(rows)
            }
            
        except Exception as e:
            logger.error(f"Power BI data export failed for {self.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refresh_dataset(self, dataset_id: str = None) -> Dict[str, Any]:
        """Trigger refresh of Power BI dataset"""
        try:
            await self._ensure_authenticated()
            
            dataset_id = dataset_id or self.config.dataset_id
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_base}/datasets/{dataset_id}/refreshes"
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            
            return {
                "success": True,
                "message": f"Dataset refresh triggered for {dataset_id}",
                "job_id": response.headers.get("RequestId")
            }
            
        except Exception as e:
            logger.error(f"Power BI dataset refresh failed for {self.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_refresh_status(self, job_id: str = None) -> Dict[str, Any]:
        """Get refresh status from Power BI"""
        try:
            await self._ensure_authenticated()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            url = f"{self.api_base}/datasets/{self.config.dataset_id}/refreshes"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            refreshes = response.json().get("value", [])
            if refreshes:
                latest_refresh = refreshes[0]  # Most recent refresh
                return {
                    "success": True,
                    "status": latest_refresh.get("status", "unknown"),
                    "start_time": latest_refresh.get("startTime"),
                    "end_time": latest_refresh.get("endTime")
                }
            
            return {
                "success": True,
                "status": "no_refresh_found"
            }
            
        except Exception as e:
            logger.error(f"Power BI refresh status check failed for {self.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Power BI connection"""
        try:
            auth_success = await self.authenticate()
            if not auth_success:
                return {
                    "success": False,
                    "error": "Authentication failed"
                }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # Test by getting dataset info
            url = f"{self.api_base}/datasets/{self.config.dataset_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            dataset_info = response.json()
            
            return {
                "success": True,
                "message": "Connection successful",
                "dataset_name": dataset_info.get("name"),
                "dataset_id": dataset_info.get("id")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class LookerConnector(BIConnectorInterface):
    """Looker connector implementation"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.api_base = config.base_url or "https://your-instance.looker.com:19999/api/4.0"
        self.access_token = None
        self.token_expires_at = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Looker API"""
        try:
            auth_url = f"{self.api_base}/login"
            
            payload = {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret
            }
            
            response = requests.post(auth_url, json=payload)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info(f"Looker authentication successful for {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Looker authentication failed for {self.name}: {e}")
            return False
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            await self.authenticate()
    
    async def export_data(self, data: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Export data to Looker (via database write)"""
        try:
            await self._ensure_authenticated()
            
            headers = {
                "Authorization": f"token {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Convert DataFrame to JSON for API upload
            data_json = data.to_json(orient="records", date_format="iso")
            
            # Use Looker's connection to write data (this would need a custom endpoint)
            url = f"{self.api_base}/connections/{self.config.workspace_id}/upload_table"
            
            payload = {
                "table_name": table_name,
                "data": json.loads(data_json)
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            return {
                "success": True,
                "message": f"Successfully exported {len(data)} rows to Looker table {table_name}",
                "record_count": len(data)
            }
            
        except Exception as e:
            logger.error(f"Looker data export failed for {self.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refresh_dataset(self, dataset_id: str = None) -> Dict[str, Any]:
        """Trigger refresh in Looker (via PDT rebuild)"""
        try:
            await self._ensure_authenticated()
            
            headers = {
                "Authorization": f"token {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Trigger PDT rebuild
            url = f"{self.api_base}/derived_tables/rebuild"
            
            payload = {
                "model_name": self.config.workspace_id,
                "view_name": dataset_id or self.config.dataset_id
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "success": True,
                "message": f"PDT rebuild triggered for {payload['view_name']}",
                "job_id": result.get("materialization_id")
            }
            
        except Exception as e:
            logger.error(f"Looker refresh failed for {self.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_refresh_status(self, job_id: str) -> Dict[str, Any]:
        """Get PDT build status from Looker"""
        try:
            await self._ensure_authenticated()
            
            headers = {
                "Authorization": f"token {self.access_token}"
            }
            
            url = f"{self.api_base}/derived_tables/{job_id}/status"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            status_info = response.json()
            
            return {
                "success": True,
                "status": status_info.get("status", "unknown"),
                "start_time": status_info.get("started_at"),
                "end_time": status_info.get("completed_at")
            }
            
        except Exception as e:
            logger.error(f"Looker status check failed for {self.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Looker connection"""
        try:
            auth_success = await self.authenticate()
            if not auth_success:
                return {
                    "success": False,
                    "error": "Authentication failed"
                }
            
            headers = {
                "Authorization": f"token {self.access_token}"
            }
            
            # Test by getting user info
            url = f"{self.api_base}/user"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            user_info = response.json()
            
            return {
                "success": True,
                "message": "Connection successful",
                "user_id": user_info.get("id"),
                "user_name": user_info.get("display_name")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class GoogleSheetsConnector(BIConnectorInterface):
    """Google Sheets connector implementation"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.service = None
        self.authenticated = False
    
    async def authenticate(self) -> bool:
        """Authenticate with Google Sheets API using service account"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            if not self.config.service_account_key:
                raise ValueError("Service account key required for Google Sheets")
            
            credentials = service_account.Credentials.from_service_account_info(
                self.config.service_account_key,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            self.service = build('sheets', 'v4', credentials=credentials)
            self.authenticated = True
            
            logger.info(f"Google Sheets authentication successful for {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Google Sheets authentication failed for {self.name}: {e}")
            return False
    
    async def export_data(self, data: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Export data to Google Sheets"""
        try:
            if not self.authenticated:
                await self.authenticate()
            
            # Convert DataFrame to values list
            values = [data.columns.tolist()]  # Header row
            for _, row in data.iterrows():
                row_values = []
                for val in row:
                    if pd.isna(val):
                        row_values.append("")
                    elif isinstance(val, (pd.Timestamp, datetime)):
                        row_values.append(val.strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        row_values.append(str(val))
                values.append(row_values)
            
            # Clear existing data and write new data
            sheet_id = self.config.dataset_id  # Google Sheets ID
            range_name = f"{table_name}!A:Z"  # Adjust range as needed
            
            # Clear the sheet first
            clear_request = self.service.spreadsheets().values().clear(
                spreadsheetId=sheet_id,
                range=range_name,
                body={}
            )
            clear_request.execute()
            
            # Write new data
            update_request = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"{table_name}!A1",
                valueInputOption="RAW",
                body={"values": values}
            )
            
            result = update_request.execute()
            
            return {
                "success": True,
                "message": f"Successfully exported {len(values)-1} rows to Google Sheets",
                "record_count": len(values) - 1,
                "updated_cells": result.get("updatedCells", 0)
            }
            
        except Exception as e:
            logger.error(f"Google Sheets export failed for {self.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refresh_dataset(self, dataset_id: str = None) -> Dict[str, Any]:
        """Refresh Google Sheets (re-export data)"""
        # For Google Sheets, refresh means re-exporting the data
        # This would typically be triggered by the scheduler
        return {
            "success": True,
            "message": "Google Sheets refresh scheduled (data will be re-exported)",
            "job_id": f"refresh_{datetime.now().timestamp()}"
        }
    
    async def get_refresh_status(self, job_id: str) -> Dict[str, Any]:
        """Get refresh status (for Google Sheets, this is always immediate)"""
        return {
            "success": True,
            "status": "completed",
            "message": "Google Sheets updates are immediate"
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Google Sheets connection"""
        try:
            if not self.authenticated:
                auth_success = await self.authenticate()
                if not auth_success:
                    return {
                        "success": False,
                        "error": "Authentication failed"
                    }
            
            # Test by getting sheet metadata
            sheet_id = self.config.dataset_id
            sheet = self.service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            
            return {
                "success": True,
                "message": "Connection successful",
                "sheet_title": sheet.get("properties", {}).get("title"),
                "sheet_id": sheet_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class BIConnectorManager:
    """Manager class for all BI connectors"""
    
    def __init__(self):
        self.connectors: Dict[str, BIConnectorInterface] = {}
        self.export_jobs: Dict[str, ExportJob] = {}
        self.refresh_schedules: Dict[str, RefreshSchedule] = {}
    
    def register_connector(self, config: ConnectorConfig) -> bool:
        """Register a new BI connector"""
        try:
            if config.connector_type == ConnectorType.POWER_BI:
                connector = PowerBIConnector(config)
            elif config.connector_type == ConnectorType.LOOKER:
                connector = LookerConnector(config)
            elif config.connector_type == ConnectorType.GOOGLE_SHEETS:
                connector = GoogleSheetsConnector(config)
            else:
                raise ValueError(f"Unsupported connector type: {config.connector_type}")
            
            self.connectors[config.name] = connector
            logger.info(f"Registered BI connector: {config.name} ({config.connector_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register connector {config.name}: {e}")
            return False
    
    def get_connector(self, name: str) -> Optional[BIConnectorInterface]:
        """Get connector by name"""
        return self.connectors.get(name)
    
    async def export_data_to_connector(self, connector_name: str, data: pd.DataFrame, 
                                     table_name: str, format: ExportFormat = ExportFormat.JSON) -> ExportJob:
        """Export data to specified connector"""
        
        job = ExportJob(
            connector_name=connector_name,
            connector_type=self.connectors[connector_name].connector_type,
            export_format=format,
            record_count=len(data)
        )
        
        self.export_jobs[job.id] = job
        
        try:
            job.status = RefreshStatus.RUNNING
            job.started_at = datetime.now()
            
            connector = self.get_connector(connector_name)
            if not connector:
                raise ValueError(f"Connector {connector_name} not found")
            
            result = await connector.export_data(data, table_name)
            
            if result.get("success"):
                job.status = RefreshStatus.SUCCESS
                job.record_count = result.get("record_count", len(data))
            else:
                job.status = RefreshStatus.FAILED
                job.error_message = result.get("error", "Unknown error")
            
        except Exception as e:
            job.status = RefreshStatus.FAILED
            job.error_message = str(e)
            logger.error(f"Export job {job.id} failed: {e}")
        
        finally:
            job.completed_at = datetime.now()
        
        return job
    
    async def refresh_connector_dataset(self, connector_name: str, dataset_id: str = None) -> Dict[str, Any]:
        """Refresh dataset in specified connector"""
        try:
            connector = self.get_connector(connector_name)
            if not connector:
                return {
                    "success": False,
                    "error": f"Connector {connector_name} not found"
                }
            
            return await connector.refresh_dataset(dataset_id)
            
        except Exception as e:
            logger.error(f"Refresh failed for {connector_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_all_connectors(self) -> Dict[str, Dict[str, Any]]:
        """Test all registered connectors"""
        results = {}
        
        for name, connector in self.connectors.items():
            try:
                results[name] = await connector.test_connection()
            except Exception as e:
                results[name] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def get_export_job(self, job_id: str) -> Optional[ExportJob]:
        """Get export job by ID"""
        return self.export_jobs.get(job_id)
    
    def list_connectors(self) -> List[Dict[str, Any]]:
        """List all registered connectors"""
        return [
            {
                "name": name,
                "type": connector.connector_type,
                "config": {
                    "workspace_id": connector.config.workspace_id,
                    "dataset_id": connector.config.dataset_id
                }
            }
            for name, connector in self.connectors.items()
        ]
    
    def add_refresh_schedule(self, schedule: RefreshSchedule):
        """Add a refresh schedule"""
        self.refresh_schedules[schedule.id] = schedule
    
    def get_refresh_schedules(self) -> List[RefreshSchedule]:
        """Get all refresh schedules"""
        return list(self.refresh_schedules.values())
    
    async def execute_scheduled_refreshes(self):
        """Execute any due scheduled refreshes"""
        current_time = datetime.now()
        
        for schedule in self.refresh_schedules.values():
            if not schedule.enabled:
                continue
                
            # Simple scheduling check (would use proper cron parsing in production)
            if schedule.next_run and current_time >= schedule.next_run:
                try:
                    result = await self.refresh_connector_dataset(schedule.connector_name)
                    schedule.last_run = current_time
                    # Calculate next run time (simplified - would use croniter in production)
                    schedule.next_run = current_time + timedelta(hours=6)  # Default 6 hours
                    
                    logger.info(f"Scheduled refresh executed for {schedule.connector_name}: {result}")
                    
                except Exception as e:
                    logger.error(f"Scheduled refresh failed for {schedule.connector_name}: {e}")

# Global manager instance
bi_connector_manager = BIConnectorManager()