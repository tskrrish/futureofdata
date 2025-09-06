"""
Test suite for BI Connectors functionality
Tests Power BI, Looker, and Google Sheets integration
"""

import asyncio
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import json

from bi_connectors import (
    BIConnectorManager,
    ConnectorConfig,
    ConnectorType,
    ExportFormat,
    RefreshStatus,
    RefreshSchedule,
    PowerBIConnector,
    LookerConnector,
    GoogleSheetsConnector
)

class TestBIConnectorManager:
    """Test the main BI Connector Manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = BIConnectorManager()
        
        # Create test configurations
        self.power_bi_config = ConnectorConfig(
            name="test_powerbi",
            connector_type=ConnectorType.POWER_BI,
            client_id="test_client_id",
            client_secret="test_client_secret",
            workspace_id="test_workspace",
            dataset_id="test_dataset"
        )
        
        self.looker_config = ConnectorConfig(
            name="test_looker",
            connector_type=ConnectorType.LOOKER,
            client_id="test_client_id",
            client_secret="test_client_secret",
            base_url="https://test.looker.com:19999/api/4.0",
            workspace_id="test_model",
            dataset_id="test_view"
        )
        
        self.google_sheets_config = ConnectorConfig(
            name="test_sheets",
            connector_type=ConnectorType.GOOGLE_SHEETS,
            dataset_id="test_sheet_id",
            service_account_key={
                "type": "service_account",
                "project_id": "test_project",
                "private_key_id": "test_key_id",
                "private_key": "-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----\n",
                "client_email": "test@test.iam.gserviceaccount.com",
                "client_id": "test_client_id",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        )
        
        # Test data
        self.test_data = pd.DataFrame({
            'volunteer_id': [1, 2, 3],
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'hours': [10.5, 25.0, 8.5],
            'last_activity': ['2024-01-15', '2024-01-20', '2024-01-18']
        })
    
    def test_register_power_bi_connector(self):
        """Test registering Power BI connector"""
        success = self.manager.register_connector(self.power_bi_config)
        assert success is True
        assert "test_powerbi" in self.manager.connectors
        assert isinstance(self.manager.connectors["test_powerbi"], PowerBIConnector)
    
    def test_register_looker_connector(self):
        """Test registering Looker connector"""
        success = self.manager.register_connector(self.looker_config)
        assert success is True
        assert "test_looker" in self.manager.connectors
        assert isinstance(self.manager.connectors["test_looker"], LookerConnector)
    
    def test_register_google_sheets_connector(self):
        """Test registering Google Sheets connector"""
        success = self.manager.register_connector(self.google_sheets_config)
        assert success is True
        assert "test_sheets" in self.manager.connectors
        assert isinstance(self.manager.connectors["test_sheets"], GoogleSheetsConnector)
    
    def test_list_connectors(self):
        """Test listing registered connectors"""
        self.manager.register_connector(self.power_bi_config)
        self.manager.register_connector(self.looker_config)
        
        connectors = self.manager.list_connectors()
        assert len(connectors) == 2
        
        connector_names = [c["name"] for c in connectors]
        assert "test_powerbi" in connector_names
        assert "test_looker" in connector_names
    
    def test_get_connector(self):
        """Test getting connector by name"""
        self.manager.register_connector(self.power_bi_config)
        
        connector = self.manager.get_connector("test_powerbi")
        assert connector is not None
        assert isinstance(connector, PowerBIConnector)
        
        missing_connector = self.manager.get_connector("nonexistent")
        assert missing_connector is None
    
    @pytest.mark.asyncio
    async def test_export_data_to_connector(self):
        """Test exporting data to connector"""
        self.manager.register_connector(self.power_bi_config)
        
        # Mock the connector's export_data method
        connector = self.manager.get_connector("test_powerbi")
        connector.export_data = AsyncMock(return_value={
            "success": True,
            "record_count": 3,
            "message": "Export successful"
        })
        
        job = await self.manager.export_data_to_connector(
            "test_powerbi",
            self.test_data,
            "volunteers",
            ExportFormat.JSON
        )
        
        assert job.status == RefreshStatus.SUCCESS
        assert job.record_count == 3
        assert job.connector_name == "test_powerbi"
        assert job.export_format == ExportFormat.JSON
    
    @pytest.mark.asyncio
    async def test_export_data_failure(self):
        """Test handling export data failure"""
        self.manager.register_connector(self.power_bi_config)
        
        # Mock the connector's export_data method to fail
        connector = self.manager.get_connector("test_powerbi")
        connector.export_data = AsyncMock(return_value={
            "success": False,
            "error": "Authentication failed"
        })
        
        job = await self.manager.export_data_to_connector(
            "test_powerbi",
            self.test_data,
            "volunteers",
            ExportFormat.JSON
        )
        
        assert job.status == RefreshStatus.FAILED
        assert "Authentication failed" in job.error_message
    
    def test_refresh_schedule_management(self):
        """Test refresh schedule management"""
        schedule = RefreshSchedule(
            connector_name="test_powerbi",
            cron_expression="0 */6 * * *",
            enabled=True
        )
        
        self.manager.add_refresh_schedule(schedule)
        schedules = self.manager.get_refresh_schedules()
        
        assert len(schedules) == 1
        assert schedules[0].connector_name == "test_powerbi"
        assert schedules[0].cron_expression == "0 */6 * * *"

class TestPowerBIConnector:
    """Test Power BI connector specifically"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = ConnectorConfig(
            name="test_powerbi",
            connector_type=ConnectorType.POWER_BI,
            client_id="test_client_id",
            client_secret="test_client_secret",
            workspace_id="test_workspace",
            dataset_id="test_dataset"
        )
        self.connector = PowerBIConnector(self.config)
    
    @patch('requests.post')
    @pytest.mark.asyncio
    async def test_authentication_success(self, mock_post):
        """Test successful Power BI authentication"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        success = await self.connector.authenticate()
        assert success is True
        assert self.connector.access_token == "test_token"
    
    @patch('requests.post')
    @pytest.mark.asyncio
    async def test_authentication_failure(self, mock_post):
        """Test Power BI authentication failure"""
        mock_post.side_effect = Exception("Authentication failed")
        
        success = await self.connector.authenticate()
        assert success is False
        assert self.connector.access_token is None
    
    @patch('requests.post')
    @patch('requests.delete')
    @pytest.mark.asyncio
    async def test_export_data_success(self, mock_delete, mock_post):
        """Test successful data export to Power BI"""
        # Mock authentication
        mock_auth_response = Mock()
        mock_auth_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }
        mock_auth_response.raise_for_status = Mock()
        
        # Mock data operations
        mock_delete.return_value = Mock()
        mock_delete.return_value.raise_for_status = Mock()
        
        mock_post.side_effect = [mock_auth_response, Mock()]
        mock_post.return_value.raise_for_status = Mock()
        
        test_data = pd.DataFrame({
            'id': [1, 2],
            'name': ['Test 1', 'Test 2']
        })
        
        result = await self.connector.export_data(test_data, "test_table")
        
        assert result["success"] is True
        assert result["record_count"] == 2

class TestLookerConnector:
    """Test Looker connector specifically"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = ConnectorConfig(
            name="test_looker",
            connector_type=ConnectorType.LOOKER,
            client_id="test_client_id",
            client_secret="test_client_secret",
            base_url="https://test.looker.com:19999/api/4.0",
            workspace_id="test_model"
        )
        self.connector = LookerConnector(self.config)
    
    @patch('requests.post')
    @pytest.mark.asyncio
    async def test_authentication_success(self, mock_post):
        """Test successful Looker authentication"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        success = await self.connector.authenticate()
        assert success is True
        assert self.connector.access_token == "test_token"
    
    @patch('requests.get')
    @pytest.mark.asyncio
    async def test_test_connection_success(self, mock_get):
        """Test successful connection test"""
        # Set up authenticated state
        self.connector.access_token = "test_token"
        self.connector.authenticated = True
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "display_name": "Test User"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = await self.connector.test_connection()
        
        assert result["success"] is True
        assert result["user_id"] == 123
        assert result["user_name"] == "Test User"

class TestGoogleSheetsConnector:
    """Test Google Sheets connector specifically"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = ConnectorConfig(
            name="test_sheets",
            connector_type=ConnectorType.GOOGLE_SHEETS,
            dataset_id="test_sheet_id",
            service_account_key={
                "type": "service_account",
                "project_id": "test_project",
                "private_key_id": "test_key_id",
                "private_key": "-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----\n",
                "client_email": "test@test.iam.gserviceaccount.com",
                "client_id": "test_client_id"
            }
        )
        self.connector = GoogleSheetsConnector(self.config)
    
    @pytest.mark.asyncio
    async def test_refresh_dataset(self):
        """Test Google Sheets refresh (immediate operation)"""
        result = await self.connector.refresh_dataset()
        
        assert result["success"] is True
        assert "job_id" in result
        assert "scheduled" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_refresh_status(self):
        """Test getting refresh status (always completed for Google Sheets)"""
        result = await self.connector.get_refresh_status("test_job_id")
        
        assert result["success"] is True
        assert result["status"] == "completed"

class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = BIConnectorManager()
        
        # Register all connector types
        configs = [
            ConnectorConfig(
                name="e2e_powerbi",
                connector_type=ConnectorType.POWER_BI,
                client_id="test_client_id",
                client_secret="test_client_secret",
                dataset_id="test_dataset"
            ),
            ConnectorConfig(
                name="e2e_looker",
                connector_type=ConnectorType.LOOKER,
                client_id="test_client_id",
                client_secret="test_client_secret",
                base_url="https://test.looker.com:19999/api/4.0"
            ),
            ConnectorConfig(
                name="e2e_sheets",
                connector_type=ConnectorType.GOOGLE_SHEETS,
                dataset_id="test_sheet_id",
                service_account_key={"type": "service_account"}
            )
        ]
        
        for config in configs:
            self.manager.register_connector(config)
    
    def test_all_connector_types_registered(self):
        """Test that all connector types are properly registered"""
        connectors = self.manager.list_connectors()
        assert len(connectors) == 3
        
        types = [c["type"] for c in connectors]
        assert ConnectorType.POWER_BI in types
        assert ConnectorType.LOOKER in types
        assert ConnectorType.GOOGLE_SHEETS in types
    
    @pytest.mark.asyncio
    async def test_multiple_export_jobs(self):
        """Test creating multiple export jobs"""
        test_data = pd.DataFrame({
            'id': [1, 2, 3],
            'value': ['A', 'B', 'C']
        })
        
        jobs = []
        for connector_name in ["e2e_powerbi", "e2e_looker", "e2e_sheets"]:
            # Mock the export_data method for each connector
            connector = self.manager.get_connector(connector_name)
            connector.export_data = AsyncMock(return_value={
                "success": True,
                "record_count": 3
            })
            
            job = await self.manager.export_data_to_connector(
                connector_name,
                test_data,
                "test_table",
                ExportFormat.JSON
            )
            jobs.append(job)
        
        assert len(jobs) == 3
        for job in jobs:
            assert job.status == RefreshStatus.SUCCESS
            assert job.record_count == 3
    
    def test_schedule_management_across_connectors(self):
        """Test managing schedules across different connector types"""
        schedules = [
            RefreshSchedule(
                connector_name="e2e_powerbi",
                cron_expression="0 */4 * * *"  # Every 4 hours
            ),
            RefreshSchedule(
                connector_name="e2e_looker",
                cron_expression="0 */8 * * *"  # Every 8 hours
            ),
            RefreshSchedule(
                connector_name="e2e_sheets",
                cron_expression="0 */2 * * *"  # Every 2 hours
            )
        ]
        
        for schedule in schedules:
            self.manager.add_refresh_schedule(schedule)
        
        all_schedules = self.manager.get_refresh_schedules()
        assert len(all_schedules) == 3
        
        cron_expressions = [s.cron_expression for s in all_schedules]
        assert "0 */4 * * *" in cron_expressions
        assert "0 */8 * * *" in cron_expressions
        assert "0 */2 * * *" in cron_expressions

# Utility functions for testing
def create_sample_volunteer_data() -> pd.DataFrame:
    """Create sample volunteer data for testing"""
    return pd.DataFrame({
        'volunteer_id': range(1, 101),
        'first_name': [f'FirstName{i}' for i in range(1, 101)],
        'last_name': [f'LastName{i}' for i in range(1, 101)],
        'email': [f'volunteer{i}@test.com' for i in range(1, 101)],
        'total_hours': [float(i * 2.5) for i in range(1, 101)],
        'branch': ['Downtown', 'North', 'South', 'East', 'West'] * 20,
        'last_activity': ['2024-01-15', '2024-01-20', '2024-01-25'] * 34 + ['2024-01-15'],
        'volunteer_type': ['Regular', 'Occasional', 'Event-based'] * 33 + ['Regular'],
        'status': ['Active'] * 100
    })

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])