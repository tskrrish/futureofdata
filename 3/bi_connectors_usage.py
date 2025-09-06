"""
Usage examples for BI Connectors
Demonstrates how to configure and use Power BI, Looker, and Google Sheets connectors
"""

import asyncio
import pandas as pd
from datetime import datetime

from bi_connectors import (
    BIConnectorManager, 
    ConnectorConfig, 
    ConnectorType, 
    ExportFormat,
    RefreshSchedule,
    bi_connector_manager
)

async def main():
    """Main usage demonstration"""
    
    print("🔗 BI Connectors Usage Examples")
    print("=" * 50)
    
    # 1. Configure Power BI Connector
    print("\n📊 Configuring Power BI Connector...")
    power_bi_config = ConnectorConfig(
        name="ymca_powerbi",
        connector_type=ConnectorType.POWER_BI,
        client_id="your-power-bi-client-id",
        client_secret="your-power-bi-client-secret",
        workspace_id="your-workspace-id",
        dataset_id="your-dataset-id"
    )
    
    success = bi_connector_manager.register_connector(power_bi_config)
    print(f"✅ Power BI connector registered: {success}")
    
    # 2. Configure Looker Connector
    print("\n📈 Configuring Looker Connector...")
    looker_config = ConnectorConfig(
        name="ymca_looker",
        connector_type=ConnectorType.LOOKER,
        client_id="your-looker-client-id",
        client_secret="your-looker-client-secret",
        base_url="https://your-instance.looker.com:19999/api/4.0",
        workspace_id="your-model-name",
        dataset_id="your-view-name"
    )
    
    success = bi_connector_manager.register_connector(looker_config)
    print(f"✅ Looker connector registered: {success}")
    
    # 3. Configure Google Sheets Connector
    print("\n📋 Configuring Google Sheets Connector...")
    
    # Service account key (would come from Google Cloud Console)
    service_account_key = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n",
        "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
    }
    
    google_sheets_config = ConnectorConfig(
        name="ymca_sheets",
        connector_type=ConnectorType.GOOGLE_SHEETS,
        dataset_id="your-google-sheet-id",  # From the sheet URL
        service_account_key=service_account_key
    )
    
    success = bi_connector_manager.register_connector(google_sheets_config)
    print(f"✅ Google Sheets connector registered: {success}")
    
    # 4. List all registered connectors
    print("\n📋 Registered Connectors:")
    connectors = bi_connector_manager.list_connectors()
    for connector in connectors:
        print(f"  - {connector['name']} ({connector['type']})")
    
    # 5. Test connections (would fail with dummy credentials)
    print("\n🔍 Testing Connections...")
    try:
        test_results = await bi_connector_manager.test_all_connectors()
        for name, result in test_results.items():
            status = "✅ Success" if result.get("success") else "❌ Failed"
            print(f"  - {name}: {status}")
            if not result.get("success"):
                print(f"    Error: {result.get('error')}")
    except Exception as e:
        print(f"  Connection tests skipped (demo mode): {e}")
    
    # 6. Create sample volunteer data
    print("\n📊 Creating Sample Volunteer Data...")
    volunteer_data = create_sample_volunteer_data()
    print(f"  Created dataset with {len(volunteer_data)} records")
    
    # 7. Export data to connectors
    print("\n📤 Exporting Data to BI Systems...")
    export_jobs = []
    
    for connector_name in ["ymca_powerbi", "ymca_looker", "ymca_sheets"]:
        try:
            job = await bi_connector_manager.export_data_to_connector(
                connector_name=connector_name,
                data=volunteer_data,
                table_name="volunteer_data",
                format=ExportFormat.JSON
            )
            export_jobs.append(job)
            print(f"  - {connector_name}: Job {job.id} ({job.status})")
        except Exception as e:
            print(f"  - {connector_name}: Export failed - {e}")
    
    # 8. Set up refresh schedules
    print("\n⏰ Setting Up Refresh Schedules...")
    
    schedules = [
        {
            "connector": "ymca_powerbi",
            "cron": "0 */6 * * *",  # Every 6 hours
            "description": "Every 6 hours"
        },
        {
            "connector": "ymca_looker", 
            "cron": "0 2 * * *",    # Daily at 2 AM
            "description": "Daily at 2 AM"
        },
        {
            "connector": "ymca_sheets",
            "cron": "0 */4 * * *",  # Every 4 hours
            "description": "Every 4 hours"
        }
    ]
    
    for schedule_info in schedules:
        schedule = RefreshSchedule(
            connector_name=schedule_info["connector"],
            cron_expression=schedule_info["cron"],
            enabled=True,
            next_run=datetime.now()
        )
        bi_connector_manager.add_refresh_schedule(schedule)
        print(f"  - {schedule_info['connector']}: {schedule_info['description']}")
    
    # 9. Manual refresh
    print("\n🔄 Manual Refresh Examples...")
    for connector_name in ["ymca_powerbi", "ymca_looker", "ymca_sheets"]:
        try:
            result = await bi_connector_manager.refresh_connector_dataset(connector_name)
            status = "✅ Success" if result.get("success") else "❌ Failed"
            print(f"  - {connector_name}: {status}")
            if result.get("job_id"):
                print(f"    Job ID: {result['job_id']}")
        except Exception as e:
            print(f"  - {connector_name}: Refresh failed - {e}")
    
    # 10. Check export job status
    print("\n📋 Export Job Status...")
    for job in export_jobs:
        print(f"  - Job {job.id}:")
        print(f"    Connector: {job.connector_name}")
        print(f"    Status: {job.status}")
        print(f"    Records: {job.record_count}")
        if job.error_message:
            print(f"    Error: {job.error_message}")
    
    print(f"\n🎉 BI Connectors demonstration complete!")
    print(f"Total connectors: {len(connectors)}")
    print(f"Export jobs: {len(export_jobs)}")
    print(f"Refresh schedules: {len(bi_connector_manager.get_refresh_schedules())}")

def create_sample_volunteer_data() -> pd.DataFrame:
    """Create sample volunteer data for demonstration"""
    import random
    from datetime import datetime, timedelta
    
    branches = ['Downtown YMCA', 'North Branch', 'East Branch', 'West Branch', 'South Branch']
    volunteer_types = ['Regular', 'Occasional', 'Event-based', 'Seasonal']
    activities = ['Youth Programs', 'Fitness Classes', 'Community Events', 'Administrative', 'Special Events']
    
    data = []
    for i in range(100):
        # Generate random volunteer data
        volunteer = {
            'volunteer_id': i + 1,
            'first_name': f'Volunteer{i+1:03d}',
            'last_name': f'Person{i+1:03d}',
            'email': f'volunteer{i+1:03d}@ymca.org',
            'phone': f'555-{random.randint(1000, 9999)}',
            'age': random.randint(16, 75),
            'gender': random.choice(['Male', 'Female', 'Other']),
            'branch': random.choice(branches),
            'volunteer_type': random.choice(volunteer_types),
            'primary_activity': random.choice(activities),
            'total_hours': round(random.uniform(5.0, 200.0), 1),
            'sessions_count': random.randint(1, 50),
            'last_activity_date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
            'registration_date': (datetime.now() - timedelta(days=random.randint(30, 1000))).strftime('%Y-%m-%d'),
            'status': random.choice(['Active', 'Inactive', 'On Hold']),
            'is_member': random.choice([True, False]),
            'emergency_contact': f'Emergency{i+1:03d} Contact',
            'emergency_phone': f'555-{random.randint(1000, 9999)}',
            'background_check_date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d') if random.random() > 0.1 else None,
            'training_completed': random.choice([True, False]),
            'preferred_schedule': random.choice(['Weekdays', 'Weekends', 'Evenings', 'Flexible']),
            'skills': ', '.join(random.sample(['Leadership', 'Teaching', 'Sports', 'Music', 'Art', 'Technology', 'Languages'], random.randint(1, 3))),
            'interests': ', '.join(random.sample(['Youth Development', 'Health & Wellness', 'Community Building', 'Education', 'Recreation'], random.randint(1, 3))),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        data.append(volunteer)
    
    return pd.DataFrame(data)

def example_api_usage():
    """
    Example of how to use the BI Connectors via API endpoints
    These would be called from your frontend or other services
    """
    
    api_examples = """
    # 1. Register a Power BI connector
    POST /api/bi-connectors/register
    {
        "name": "ymca_powerbi",
        "connector_type": "power_bi",
        "client_id": "your-client-id",
        "client_secret": "your-client-secret",
        "workspace_id": "your-workspace-id",
        "dataset_id": "your-dataset-id"
    }
    
    # 2. List all connectors
    GET /api/bi-connectors
    
    # 3. Test a specific connector
    POST /api/bi-connectors/ymca_powerbi/test
    
    # 4. Export data to BI system
    POST /api/bi-connectors/export
    {
        "connector_name": "ymca_powerbi",
        "table_name": "volunteer_data",
        "export_format": "json"
    }
    
    # 5. Check export job status
    GET /api/bi-connectors/export-jobs/{job_id}
    
    # 6. Manually refresh dataset
    POST /api/bi-connectors/ymca_powerbi/refresh
    
    # 7. Create refresh schedule
    POST /api/bi-connectors/schedules
    {
        "connector_name": "ymca_powerbi",
        "cron_expression": "0 */6 * * *",
        "enabled": true
    }
    
    # 8. List all schedules
    GET /api/bi-connectors/schedules
    
    # 9. Remove a connector
    DELETE /api/bi-connectors/ymca_powerbi
    """
    
    print("API Usage Examples:")
    print(api_examples)

if __name__ == "__main__":
    print("Running BI Connectors Usage Examples...")
    print("Note: This demo uses placeholder credentials and will show connection failures")
    print("In production, replace with real credentials from your BI systems\n")
    
    # Run the async demo
    asyncio.run(main())
    
    print("\n" + "="*50)
    example_api_usage()